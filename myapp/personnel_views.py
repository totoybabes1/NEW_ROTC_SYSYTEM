from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Personnel, Profile, UserActivity, Announcement, UploadedData, AttendanceRecord
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Avg

def personnel_login(request):
    if request.user.is_authenticated:
        return redirect('personnel_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, 'personnel'):
            login(request, user)
            # Record login activity
            UserActivity.objects.create(user=user, activity_type='login')
            return redirect('personnel_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'personnel/login.html')

def personnel_logout(request):
    if request.user.is_authenticated:
        # Record logout activity
        UserActivity.objects.create(user=request.user, activity_type='logout')
    logout(request)
    return redirect('personnel_login')

@login_required(login_url='personnel_login')
def personnel_dashboard(request):
    personnel = Personnel.objects.get(user=request.user)
    
    # Get existing data
    recent_activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:5]
    total_logins = UserActivity.objects.filter(user=request.user, activity_type='login').count()
    
    # Get attendance data using new models
    recent_attendance = AttendanceRecord.objects.filter(
        personnel=personnel
    ).select_related('uploaded_data').order_by('-marked_at')[:5]
    
    # Calculate attendance statistics
    total_records = AttendanceRecord.objects.filter(personnel=personnel).count()
    present_count = AttendanceRecord.objects.filter(personnel=personnel, status='PRESENT').count()
    absent_count = AttendanceRecord.objects.filter(personnel=personnel, status='ABSENT').count()
    late_count = AttendanceRecord.objects.filter(personnel=personnel, status='LATE').count()
    
    attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
    
    context = {
        'personnel': personnel,
        'recent_activities': recent_activities,
        'total_logins': total_logins,
        'recent_attendance': recent_attendance,
        'attendance_stats': {
            'total': total_records,
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'rate': round(attendance_rate, 2)
        }
    }
    return render(request, 'personnel/dashboard.html', context)

@login_required(login_url='personnel_login')
def personnel_profile(request):
    personnel = Personnel.objects.get(user=request.user)
    
    if request.method == 'POST':
        # Handle profile picture update
        if 'profile_picture' in request.FILES:
            personnel.profile_picture = request.FILES['profile_picture']
            personnel.save()
            messages.success(request, 'Profile picture updated successfully.')
            return redirect('personnel_profile')
        
        # Handle password change
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if current_password and new_password:
            # Verify current password
            if request.user.check_password(current_password):
                if new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    messages.success(request, 'Password updated successfully. Please login again.')
                    return redirect('personnel_login')
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        # Update contact information
        phone_number = request.POST.get('phone_number')
        if phone_number:
            personnel.phone_number = phone_number
            personnel.save()
            messages.success(request, 'Profile updated successfully.')
        
    return render(request, 'personnel/profile.html', {'personnel': personnel}) 