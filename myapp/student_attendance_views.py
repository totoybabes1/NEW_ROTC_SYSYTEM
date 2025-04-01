from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Personnel, StudentRecord, PersonnelStudentAssignment, StudentAttendance
from datetime import datetime

@login_required(login_url='personnel_login')
def record_attendance(request):
    """View for recording student attendance"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        assignments = PersonnelStudentAssignment.objects.filter(personnel=personnel).select_related('student')
        
        if request.method == 'POST':
            date_str = request.POST.get('date')
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Invalid date format.")
                return redirect('record_attendance')
            
            # Process attendance data
            for assignment in assignments:
                student_id = assignment.student.id
                status = request.POST.get(f'status_{student_id}')
                remarks = request.POST.get(f'remarks_{student_id}', '')
                
                if status:
                    # Check if attendance record already exists for this student and date
                    attendance, created = StudentAttendance.objects.update_or_create(
                        student_id=student_id,
                        personnel=personnel,
                        date=attendance_date,
                        defaults={
                            'status': status,
                            'remarks': remarks
                        }
                    )
            
            messages.success(request, 'Attendance recorded successfully.')
            return redirect('record_attendance')
        
        context = {
            'personnel': personnel,
            'assignments': assignments,
            'today': datetime.now().strftime('%Y-%m-%d')
        }
        return render(request, 'personnel/record_attendance.html', context)
    except Personnel.DoesNotExist:
        messages.error(request, "Personnel profile not found.")
        return redirect('personnel_login')

@login_required(login_url='personnel_login')
def view_attendance(request):
    """View for displaying attendance records"""
    personnel = get_object_or_404(Personnel, user=request.user)
    attendance_records = StudentAttendance.objects.filter(personnel=personnel).select_related('student').order_by('-date')
    
    context = {
        'personnel': personnel,
        'attendance_records': attendance_records
    }
    return render(request, 'personnel/view_attendance.html', context)

@login_required(login_url='personnel_login')
def get_student_attendance(request, student_id):
    """API endpoint to get student attendance data for grade computation"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        
        # Get total attendance records
        total_records = StudentAttendance.objects.filter(
            student_id=student_id,
            personnel=personnel
        ).count()
        
        # Get present records (assuming 'present' is the status value for present)
        present_records = StudentAttendance.objects.filter(
            student_id=student_id,
            personnel=personnel,
            status='present'
        ).count()
        
        # Calculate attendance percentage
        attendance_percentage = 0
        if total_records > 0:
            attendance_percentage = (present_records / total_records) * 100
        
        return JsonResponse({
            'success': True,
            'total_days': total_records,
            'days_present': present_records,
            'attendance_percentage': round(attendance_percentage, 2)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}) 