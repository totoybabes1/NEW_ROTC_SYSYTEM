from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Personnel, Profile, UserActivity, Announcement
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
    
    # Get user's activities
    recent_activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:5]
    
    # Calculate activity statistics
    total_logins = UserActivity.objects.filter(user=request.user, activity_type='login').count()
    
    # Calculate days active (unique days with activity)
    unique_days = UserActivity.objects.filter(user=request.user).dates('timestamp', 'day')
    days_active = len(unique_days)
    
    # Calculate days since last activity
    last_activity = UserActivity.objects.filter(user=request.user).order_by('-timestamp').first()
    last_active_days = 0
    if last_activity:
        last_active_days = (timezone.now().date() - last_activity.timestamp.date()).days

    # Get flight group members
    flight_group_members = Personnel.objects.filter(
        flight_group=personnel.flight_group
    ).exclude(id=personnel.id)

    # Get announcements and upcoming events
    announcements = Announcement.objects.filter(
        flight_group=personnel.flight_group,
        date__gte=timezone.now() - timedelta(days=30)
    ).order_by('-date')[:5]

    # Calculate attendance rate (example calculation)
    total_days = 30  # Last 30 days
    present_days = UserActivity.objects.filter(
        user=request.user,
        timestamp__gte=timezone.now() - timedelta(days=total_days)
    ).dates('timestamp', 'day').count()
    attendance_rate = int((present_days / total_days) * 100)

    # Calculate participation score (example calculation)
    participation_score = 85  # This would be calculated based on your specific metrics

    # Generate attendance calendar data
    attendance_calendar = []
    today = timezone.now().date()
    for i in range(30):
        date = today - timedelta(days=i)
        present = UserActivity.objects.filter(
            user=request.user,
            timestamp__date=date
        ).exists()
        attendance_calendar.append({
            'date': date,
            'present': present
        })
    attendance_calendar.reverse()
    
    context = {
        'personnel': personnel,
        'flight_group': personnel.flight_group,
        'recent_activities': recent_activities,
        'total_logins': total_logins,
        'days_active': days_active,
        'last_active_days': last_active_days,
        'flight_group_members': flight_group_members,
        'announcements': announcements,
        'attendance_rate': attendance_rate,
        'participation_score': participation_score,
        'attendance_calendar': attendance_calendar,
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