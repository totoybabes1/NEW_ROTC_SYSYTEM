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
        
        # Try to get today's attendance records safely
        try:
            today_attendance = StudentAttendance.objects.filter(
                personnel=personnel,
                date=today
            )
            
            # Calculate stats
            stats = {
                'total_students': assignments.count(),
                'present_today': today_attendance.filter(status='PRESENT').count(),
                'late_today': today_attendance.filter(status='LATE').count(),
                'absent_today': today_attendance.filter(status='ABSENT').count(),
                'excused_today': today_attendance.filter(status='EXCUSED').count(),
            }
        except Exception as e:
            # If there's an error, use empty stats
            stats = {
                'total_students': assignments.count(),
                'present_today': 0,
                'late_today': 0,
                'absent_today': 0,
                'excused_today': 0,
            }
            today_attendance = []
            messages.error(request, f"Database error: {str(e)}. Please run migrations to fix this issue.")
        
        # Get all assigned students for the dropdown
        assigned_students = [assignment.student for assignment in assignments]
        
        context = {
            'personnel': personnel,
            'stats': stats,
            'assignments': assignments,
            'assigned_students': assigned_students,
            'today_attendance': today_attendance,
            'today': today,
        }
        
        return render(request, 'personnel/attendance_dashboard.html', context)
    except Personnel.DoesNotExist:
        messages.error(request, "Personnel profile not found.")
        return redirect('personnel_login')

@login_required
def record_attendance(request):
    if request.method == 'POST':
        try:
            personnel = Personnel.objects.get(user=request.user)
            student_id = request.POST.get('student_id')
            date_str = request.POST.get('date')
            status = request.POST.get('status')
            time_in = request.POST.get('time_in', '')
            time_out = request.POST.get('time_out', '')
            remarks = request.POST.get('remarks', '')
            
            # Validate required fields
            if not all([student_id, date_str, status]):
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required fields'
                })
            
            # Get the student
            student = StudentRecord.objects.get(id=student_id)
            
            # Verify this student is assigned to this personnel
            if not PersonnelStudentAssignment.objects.filter(personnel=personnel, student=student).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'This student is not assigned to you'
                })
            
            # Parse date
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Check if record already exists for this student and date
            attendance, created = StudentAttendance.objects.update_or_create(
                student=student,
                date=date,
                defaults={
                    'personnel': personnel,
                    'status': status,
                    'time_in': time_in if time_in else None,
                    'time_out': time_out if time_out else None,
                    'remarks': remarks
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Attendance recorded successfully'
            })
        except Personnel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Personnel not found'
            })
        except StudentRecord.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
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
            time_in = request.POST.get('time_in')
            time_out = request.POST.get('time_out')
            status = request.POST.get('status')
            remarks = request.POST.get('remarks')
            
            # Get the attendance record
            attendance = StudentAttendance.objects.get(id=record_id)
            
            # Verify this personnel has permission to update this record
            if attendance.personnel != personnel:
                return JsonResponse({
                    'success': False,
                    'message': 'You do not have permission to update this record'
                })
            
            # Update the record
            attendance.time_in = time_in if time_in else None
            attendance.time_out = time_out if time_out else None
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
            
            # Base query
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
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    attendance_records = attendance_records.filter(date__range=[start, end])
                except ValueError:
                    pass  # Invalid date format, ignore filter
            
            # Calculate stats
            stats = {
                'total_records': attendance_records.count(),
                'present_count': attendance_records.filter(status='PRESENT').count(),
                'late_count': attendance_records.filter(status='LATE').count(),
                'absent_count': attendance_records.filter(status='ABSENT').count(),
                'excused_count': attendance_records.filter(status='EXCUSED').count(),
            }
            
            # Get all assigned students for the dropdown
            assigned_students = [assignment.student for assignment in assignments]
            
            context = {
                'personnel': personnel,
                'stats': stats,
                'attendance_records': attendance_records,
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
                'time_in': record.time_in.strftime('%H:%M') if record.time_in else None,
                'time_out': record.time_out.strftime('%H:%M') if record.time_out else None,
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
            
            # Parse JSON data from request body
            data = json.loads(request.body)
            attendance_records = data.get('attendance_records', [])
            
            success_count = 0
            error_count = 0
            
            for record in attendance_records:
                try:
                    student_id = record.get('student_id')
                    date_str = record.get('date')
                    status = record.get('status')
                    time_in = record.get('time_in')
                    remarks = record.get('remarks', '')
                    
                    # Skip if missing required fields
                    if not all([student_id, date_str, status]):
                        error_count += 1
                        continue
                    
                    # Get the student
                    student = StudentRecord.objects.get(id=student_id)
                    
                    # Verify this student is assigned to this personnel
                    if not PersonnelStudentAssignment.objects.filter(personnel=personnel, student=student).exists():
                        error_count += 1
                        continue
                    
                    # Parse date
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Update or create attendance record
                    StudentAttendance.objects.update_or_create(
                        student=student,
                        date=date,
                        defaults={
                            'personnel': personnel,
                            'status': status,
                            'time_in': time_in if time_in else None,
                            'time_out': None,  # Can be updated later
                            'remarks': remarks
                        }
                    )
                    
                    success_count += 1
                except Exception:
                    error_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully recorded {success_count} attendance records. {error_count} records had errors.'
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