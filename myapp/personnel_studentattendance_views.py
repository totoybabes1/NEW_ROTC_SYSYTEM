from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Personnel, StudentAttendance, PersonnelStudentAssignment, StudentRecord
from django.contrib import messages
import json

@login_required
def attendance_dashboard(request):
    try:
        personnel = Personnel.objects.get(user=request.user)
        assignments = PersonnelStudentAssignment.objects.filter(personnel=personnel)
        
        # Get today's date
        today = timezone.now().date()
        
        # Get attendance statistics
        total_students = assignments.count()
        present_today = StudentAttendance.objects.filter(
            student__in=[a.student for a in assignments],
            personnel=personnel,
            date=today,
            is_activity=False,
            status='PRESENT'
        ).count()
        
        late_today = StudentAttendance.objects.filter(
            student__in=[a.student for a in assignments],
            personnel=personnel,
            date=today,
            is_activity=False,
            status='LATE'
        ).count()
        
        absent_today = StudentAttendance.objects.filter(
            student__in=[a.student for a in assignments],
            personnel=personnel,
            date=today,
            is_activity=False,
            status='ABSENT'
        ).count()
        
        # Get recent records (both attendance and activities)
        recent_records = StudentAttendance.objects.filter(
            personnel=personnel,
            student__in=[a.student for a in assignments]
        ).order_by('-date', '-created_at')[:20]
        
        context = {
            'personnel': personnel,
            'assignments': assignments,
            'stats': {
                'total_students': total_students,
                'present_today': present_today,
                'late_today': late_today,
                'absent_today': absent_today,
                'unrecorded': total_students - (present_today + late_today + absent_today)
            },
            'today': today,
            'recent_records': recent_records
        }
        
        return render(request, 'personnel/attendance_dashboard.html', context)
    except Personnel.DoesNotExist:
        messages.error(request, "Personnel profile not found.")
        return redirect('personnel_login')

@login_required
def record_attendance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            date_str = data.get('date')
            time_in = data.get('time_in')
            time_out = data.get('time_out')
            status = data.get('status')
            remarks = data.get('remarks')
            
            # Convert date string to date object
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get student
            student = StudentRecord.objects.get(id=student_id)
            
            # Check if attendance record already exists for this student and date
            attendance, created = StudentAttendance.objects.get_or_create(
                student=student,
                date=date,
                is_activity=False,
                defaults={
                    'time_in': time_in if time_in else None,
                    'time_out': time_out if time_out else None,
                    'status': status,
                    'remarks': remarks
                }
            )
            
            if not created:
                # Update existing record
                attendance.time_in = time_in if time_in else None
                attendance.time_out = time_out if time_out else None
                attendance.status = status
                attendance.remarks = remarks
                attendance.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Attendance recorded successfully',
                'id': attendance.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
def record_activity(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            date_str = data.get('date')
            sf = data.get('sf')
            cadet_sign = data.get('cadet_sign', '')
            activity_description = data.get('activity_description')
            merits = data.get('merits', 0)
            demerits = data.get('demerits', 0)
            
            # Convert date string to date object
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get student
            student = StudentRecord.objects.get(id=student_id)
            
            # Create activity record
            activity = StudentAttendance.objects.create(
                student=student,
                date=date,
                is_activity=True,
                status='PRESENT',  # Default status for activities
                sf=sf,
                cadet_sign=cadet_sign,
                activity_description=activity_description,
                merits=merits,
                demerits=demerits
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Activity recorded successfully',
                'id': activity.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
def check_attendance_exists(request):
    """Check if attendance record exists for a student on a specific date"""
    if request.method == 'GET':
        try:
            student_id = request.GET.get('student_id')
            date_str = request.GET.get('date')
            
            # Parse date
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Check if record exists
            exists = StudentAttendance.objects.filter(
                student_id=student_id,
                date=date
            ).exists()
            
            return JsonResponse({
                'success': True,
                'exists': exists
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
def update_attendance(request):
    """Update an existing attendance record"""
    if request.method == 'POST':
        try:
            personnel = Personnel.objects.get(user=request.user)
            record_id = request.POST.get('record_id')
            time_in = request.POST.get('time_in', '')
            time_out = request.POST.get('time_out', '')
            status = request.POST.get('status')
            remarks = request.POST.get('remarks', '')
            
            # Get the attendance record
            attendance = StudentAttendance.objects.get(id=record_id)
            
            # Verify this personnel has permission to update this record
            if attendance.personnel != personnel:
                return JsonResponse({
                    'success': False,
                    'message': 'You do not have permission to update this record'
                })
            
            # Debug information
            print(f"Updating record {record_id}")
            print(f"Time in: '{time_in}', Time out: '{time_out}'")
            
            # Update the record - handle empty strings properly
            attendance.time_in = None if not time_in else time_in
            attendance.time_out = None if not time_out else time_out
            attendance.status = status
            attendance.remarks = remarks
            attendance.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Attendance record updated successfully.'
            })
        except StudentAttendance.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Attendance record not found.'
            })
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

@login_required
def view_attendance_history(request):
    try:
        personnel = Personnel.objects.get(user=request.user)
        assignments = PersonnelStudentAssignment.objects.filter(personnel=personnel)
        
        # Try to get attendance records safely
        try:
            # Get filter parameters
            student_id = request.GET.get('student_id')
            status = request.GET.get('status')
            date_range = request.GET.get('dateRange')
            
            # Base query - only get records for this personnel
            attendance_records = StudentAttendance.objects.filter(personnel=personnel)
            
            # Apply filters if provided
            if student_id:
                attendance_records = attendance_records.filter(student_id=student_id)
            
            if status:
                attendance_records = attendance_records.filter(status=status)
            
            if date_range:
                # Parse date range and filter
                try:
                    start_date, end_date = date_range.split(' - ')
                    start = datetime.strptime(start_date, '%m/%d/%Y').date()
                    end = datetime.strptime(end_date, '%m/%d/%Y').date()
                    attendance_records = attendance_records.filter(date__range=[start, end])
                except ValueError:
                    pass  # Invalid date format, ignore filter
            
            # Calculate stats based on filtered records
            stats = {
                'total_records': attendance_records.count(),
                'present_count': attendance_records.filter(status='PRESENT').count(),
                'late_count': attendance_records.filter(status='LATE').count(),
                'absent_count': attendance_records.filter(status='ABSENT').count(),
                'excused_count': attendance_records.filter(status='EXCUSED').count(),
            }
            
            # Get all assigned students for the dropdown
            assigned_students = [assignment.student for assignment in assignments]
            
            # Don't process records - pass them directly to the template
            # This avoids any potential issues with the time_out field
            
            context = {
                'personnel': personnel,
                'stats': stats,
                'attendance_records': attendance_records,  # Pass the queryset directly
                'assigned_students': assigned_students,
                'assignments': assignments,
                'filters': {
                    'student_id': student_id,
                    'status': status,
                    'date_range': date_range,
                }
            }
            
            return render(request, 'personnel/attendance_history.html', context)
        except Exception as e:
            messages.error(request, f"Error retrieving attendance records: {str(e)}")
            return render(request, 'personnel/attendance_history.html', {
                'personnel': personnel,
                'error': str(e)
            })
    except Personnel.DoesNotExist:
        messages.error(request, "Personnel profile not found.")
        return redirect('personnel_login')

@login_required
def get_student_attendance(request, student_id):
    """Get attendance history for a specific student"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        student = get_object_or_404(StudentRecord, id=student_id)
        
        # Verify this student is assigned to this personnel
        if not PersonnelStudentAssignment.objects.filter(personnel=personnel, student=student).exists():
            return JsonResponse({
                'success': False,
                'message': 'This student is not assigned to you'
            })
        
        # Get attendance records
        attendance_records = StudentAttendance.objects.filter(
            student=student,
            personnel=personnel
        ).order_by('-date')
        
        # Format records for JSON response
        records = []
        for record in attendance_records:
            records.append({
                'id': record.id,
                'date': record.date.strftime('%Y-%m-%d'),
                'status': record.status,
                'time_in': record.time_in if record.time_in else '',
                'time_out': record.time_out if record.time_out else '',
                'remarks': record.remarks
            })
        
        return JsonResponse({
            'success': True,
            'student': {
                'id': student.id,
                'name': student.name,
                'student_no': student.student_no
            },
            'records': records
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def batch_record_attendance(request):
    """Record attendance for multiple students at once"""
    if request.method == 'POST':
        try:
            personnel = Personnel.objects.get(user=request.user)
            data = json.loads(request.body)
            student_ids = data.get('student_ids', [])
            date_str = data.get('date')
            status = data.get('status')
            time_in = data.get('time_in', '')
            time_out = data.get('time_out', '')
            
            # Debug information
            print(f"Batch recording for {len(student_ids)} students")
            print(f"Time in: '{time_in}', Time out: '{time_out}'")
            
            if not student_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'No students selected'
                })
            
            # Validate date
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid date format'
                })
            
            # Process each student
            created_count = 0
            updated_count = 0
            
            # Convert empty strings to None for time fields
            time_in_value = None if not time_in else time_in
            time_out_value = None if not time_out else time_out
            
            for student_id in student_ids:
                try:
                    student = StudentRecord.objects.get(id=student_id)
                    
                    # Check if attendance already exists
                    existing_attendance = StudentAttendance.objects.filter(
                        student=student,
                        personnel=personnel,
                        date=attendance_date
                    ).first()
                    
                    if existing_attendance:
                        # Update existing record
                        existing_attendance.status = status
                        
                        # Only update time fields if provided
                        if time_in:
                            existing_attendance.time_in = time_in_value
                        if time_out:
                            existing_attendance.time_out = time_out_value
                            
                        existing_attendance.save()
                        updated_count += 1
                    else:
                        # Create new record
                        StudentAttendance.objects.create(
                            student=student,
                            personnel=personnel,
                            date=attendance_date,
                            status=status,
                            time_in=time_in_value,
                            time_out=time_out_value
                        )
                        created_count += 1
                        
                except StudentRecord.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully recorded attendance for {created_count} students and updated {updated_count} existing records.'
            })
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
def batch_update_attendance(request):
    """Update multiple attendance records at once"""
    if request.method == 'POST':
        try:
            personnel = Personnel.objects.get(user=request.user)
            
            # Parse JSON data from request body
            data = json.loads(request.body)
            record_ids = data.get('record_ids', [])
            date = data.get('date')
            status = data.get('status')
            time_in = data.get('time_in')
            time_out = data.get('time_out')
            
            if not record_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'No records selected for update'
                })
            
            if not any([date, status, time_in, time_out]):
                return JsonResponse({
                    'success': False,
                    'message': 'No update fields provided'
                })
            
            # Get records that belong to students assigned to this personnel
            assigned_student_ids = PersonnelStudentAssignment.objects.filter(
                personnel=personnel
            ).values_list('student_id', flat=True)
            
            records_to_update = StudentAttendance.objects.filter(
                id__in=record_ids,
                student_id__in=assigned_student_ids
            )
            
            update_count = 0
            
            # Update each record with the provided fields
            for record in records_to_update:
                if date:
                    record.date = datetime.strptime(date, '%Y-%m-%d').date()
                if status:
                    record.status = status
                if time_in:
                    record.time_in = time_in
                if time_out:
                    record.time_out = time_out
                
                record.save()
                update_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully updated {update_count} attendance records.'
            })
            
        except Personnel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Personnel not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
def get_student_attendance_summary(request, student_id):
    """Get attendance summary statistics for a specific student"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        student = get_object_or_404(StudentRecord, id=student_id)
        
        # Verify this student is assigned to this personnel
        if not PersonnelStudentAssignment.objects.filter(personnel=personnel, student=student).exists():
            return JsonResponse({
                'success': False,
                'message': 'This student is not assigned to you'
            })
        
        # Get attendance records
        attendance_records = StudentAttendance.objects.filter(
            student=student,
            personnel=personnel
        )
        
        # Calculate statistics
        total_periods = attendance_records.count()
        present_count = attendance_records.filter(status='PRESENT').count()
        absent_count = attendance_records.filter(status='ABSENT').count()
        late_count = attendance_records.filter(status='LATE').count()
        excused_count = attendance_records.filter(status='EXCUSED').count()
        
        # Calculate attendance percentage
        attendance_percentage = (present_count / total_periods * 100) if total_periods > 0 else 0
        
        return JsonResponse({
            'success': True,
            'total_periods': total_periods,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'excused_count': excused_count,
            'attendance_percentage': round(attendance_percentage, 2)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def view_students_assigned(request):
    """View students assigned to the logged-in personnel"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        assignments = PersonnelStudentAssignment.objects.filter(personnel=personnel)
        
        # Get statistics
        total_students = assignments.count()
        
        # Group students by course
        students_by_course = {}
        for assignment in assignments:
            course = assignment.student.course
            if course not in students_by_course:
                students_by_course[course] = []
            students_by_course[course].append(assignment.student)
        
        # Get all assigned students
        assigned_students = [assignment.student for assignment in assignments]
        
        context = {
            'personnel': personnel,
            'assignments': assignments,
            'assigned_students': assigned_students,
            'total_students': total_students,
            'students_by_course': students_by_course,
        }
        
        return render(request, 'personnel/students_assigned.html', context)
    except Personnel.DoesNotExist:
        messages.error(request, "Personnel profile not found.")
        return redirect('personnel_login')