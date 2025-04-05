from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .models import StudentRecord, StudentAttendance, StudentGrade, StudentActivity, StudentAccountChange
from django.db.models import Sum
from django.contrib.auth.models import User

def student_login(request):
    if request.method == 'POST':
        student_no = request.POST.get('student_no')
        password = request.POST.get('password')
        
        # You'll need to implement proper authentication here
        # This is a basic example
        try:
            student = StudentRecord.objects.get(student_no=student_no)
            user = authenticate(request, username=student_no, password=password)
            if user is not None:
                login(request, user)
                return redirect('student_dashboard')
            else:
                messages.error(request, 'Invalid credentials')
        except StudentRecord.DoesNotExist:
            messages.error(request, 'Student not found')
            
    return render(request, 'student/login.html')

@login_required
def student_dashboard(request):
    try:
        # Get the student record based on the logged-in user's username (student number)
        student = StudentRecord.objects.get(student_no=request.user.username)
        
        # Get attendance records
        attendance = StudentAttendance.objects.filter(student=student).order_by('-date')[:5]
        
        # Get latest grades
        grades = StudentGrade.objects.filter(student=student).order_by('-date_computed')[:1]
        
        # Get merits and demerits
        activities = StudentActivity.objects.filter(student=student)
        total_merits = activities.aggregate(Sum('merits'))['merits__sum'] or 0
        total_demerits = activities.aggregate(Sum('demerits'))['demerits__sum'] or 0
        
        context = {
            'student': student,
            'attendance': attendance,
            'grades': grades,
            'total_merits': total_merits,
            'total_demerits': total_demerits,
            'recent_activities': activities.order_by('-date')[:5]
        }
        
        return render(request, 'student/dashboard.html', context)
    except StudentRecord.DoesNotExist:
        messages.error(request, 'Student record not found')
        logout(request)
        return redirect('student_login')

def student_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')

@login_required
def student_profile(request):
    try:
        # Get the student record based on the logged-in user's username
        student = StudentRecord.objects.get(student_no=request.user.username)
        
        if request.method == 'POST':
            # Handle form submission
            current_password = request.POST.get('current_password')
            new_username = request.POST.get('username')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Verify current password
            user = authenticate(username=request.user.username, password=current_password)
            
            if user is not None:
                # Process username change if needed
                if new_username and new_username != request.user.username:
                    # Check if username is already taken
                    if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                        messages.error(request, 'Username already taken.')
                    else:
                        old_username = request.user.username
                        request.user.username = new_username
                        request.user.save()
                        
                        # Log the username change
                        StudentAccountChange.objects.create(
                            student=student,
                            action=f"Changed username from {old_username} to {new_username}"
                        )
                        
                        messages.success(request, 'Username updated successfully.')
                
                # Process password change if needed
                if new_password:
                    if new_password == confirm_password:
                        request.user.set_password(new_password)
                        request.user.save()
                        
                        # Log the password change
                        StudentAccountChange.objects.create(
                            student=student,
                            action="Changed password"
                        )
                        
                        # Update session to prevent logout
                        update_session_auth_hash(request, request.user)
                        
                        messages.success(request, 'Password updated successfully.')
                    else:
                        messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        # Get account change history
        account_changes = StudentAccountChange.objects.filter(student=student)
        
        context = {
            'student': student,
            'user': request.user,
            'account_changes': account_changes
        }
        
        return render(request, 'student/student_profile.html', context)
    except StudentRecord.DoesNotExist:
        messages.error(request, 'Student record not found')
        logout(request)
        return redirect('student_login')

@login_required
def student_attendance(request):
    try:
        # Get the student record based on the logged-in user's username
        student = StudentRecord.objects.get(student_no=request.user.username)
        
        # Get all attendance records for the student
        attendance_records = StudentAttendance.objects.filter(student=student).order_by('-date')
        
        # Calculate attendance statistics
        total_records = attendance_records.count()
        present_count = attendance_records.filter(status='present').count()
        absent_count = attendance_records.filter(status='absent').count()
        late_count = attendance_records.filter(status='late').count()
        excused_count = attendance_records.filter(status='excused').count()
        
        # Calculate attendance percentage if there are records
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
        
        context = {
            'student': student,
            'attendance_records': attendance_records,
            'total_records': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'excused_count': excused_count,
            'attendance_percentage': attendance_percentage
        }
        
        return render(request, 'student/attendance.html', context)
    except StudentRecord.DoesNotExist:
        messages.error(request, 'Student record not found')
        logout(request)
        return redirect('student_login')

@login_required
def student_activities(request):
    try:
        # Get the student record based on the logged-in user's username
        student = StudentRecord.objects.get(student_no=request.user.username)
        
        # Get all activity records for the student
        activities = StudentActivity.objects.filter(student=student).order_by('-date')
        
        # Calculate total merits and demerits
        total_merits = activities.aggregate(Sum('merits'))['merits__sum'] or 0
        total_demerits = activities.aggregate(Sum('demerits'))['demerits__sum'] or 0
        
        # Calculate net score
        net_score = total_merits - total_demerits
        
        context = {
            'student': student,
            'activities': activities,
            'total_merits': total_merits,
            'total_demerits': total_demerits,
            'net_score': net_score
        }
        
        return render(request, 'student/activities.html', context)
    except StudentRecord.DoesNotExist:
        messages.error(request, 'Student record not found')
        logout(request)
        return redirect('student_login') 