from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Personnel, Profile, UserActivity
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Avg
from django.views.decorators.cache import cache_page
from django.core.cache import cache

def personnel_login(request):
    if request.user.is_authenticated:
        return redirect('personnel_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Add validation for empty fields
        if not username:
            messages.error(request, 'Username is required.')
            return render(request, 'personnel/login.html')
        if not password:
            messages.error(request, 'Password is required.')
            return render(request, 'personnel/login.html')
            
        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, 'personnel'):
            login(request, user)
            # Record login activity
            UserActivity.objects.create(user=user, activity_type='login')
            messages.success(request, f'Welcome back, {user.username}!')
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

@cache_page(60 * 5)  # Cache for 5 minutes
def personnel_dashboard(request):
    personnel = get_object_or_404(Personnel, user=request.user)
    
    # Check if it's an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'personnel/dashboard_content.html', {
            'personnel': personnel,
        })
    
    return render(request, 'personnel/dashboard.html', {
        'personnel': personnel,
    })

@login_required(login_url='personnel_login')
def personnel_profile(request):
    personnel = Personnel.objects.get(user=request.user)
    
    if request.method == 'POST':
        # Handle profile picture update
        if 'profile_picture' in request.FILES:
            profile_pic = request.FILES['profile_picture']
            # Validate file size (limit to 5MB)
            if profile_pic.size > 5 * 1024 * 1024:
                messages.error(request, 'Profile picture size should not exceed 5MB.')
                return redirect('personnel_profile')
            # Validate file type
            if not profile_pic.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                messages.error(request, 'Only PNG, JPG, and JPEG files are allowed for profile pictures.')
                return redirect('personnel_profile')
                
            personnel.profile_picture = profile_pic
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
                    # Validate password strength
                    if len(new_password) < 8:
                        messages.error(request, 'Password must be at least 8 characters long.')
                    elif new_password.isdigit() or new_password.isalpha():
                        messages.error(request, 'Password must contain both letters and numbers.')
                    else:
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
            # Validate phone number format (simple validation)
            if not phone_number.isdigit() or len(phone_number) < 10:
                messages.error(request, 'Please enter a valid phone number with at least 10 digits.')
            else:
                personnel.phone_number = phone_number
                personnel.save()
                messages.success(request, 'Phone number updated successfully.')
        else:
            if 'phone_number' in request.POST:  # Check if field was submitted but empty
                messages.warning(request, 'Phone number field was left empty.')
        
    return render(request, 'personnel/profile.html', {'personnel': personnel})

@login_required(login_url='personnel_login')
def attendance_dashboard(request):
    try:
        personnel = Personnel.objects.get(user=request.user)
        
        # Get recent activities
        recent_activities = StudentActivity.objects.filter(
            personnel=personnel
        ).select_related('student').order_by('-date')[:10]
        
        if not recent_activities:
            messages.info(request, 'No recent attendance activities found.')
        
        context = {
            'personnel': personnel,
            'recent_activities': recent_activities,
        }
        
        return render(request, 'personnel/attendance_dashboard.html', context)
    except Personnel.DoesNotExist:
        messages.error(request, 'Personnel profile not found. Please contact an administrator.')
        return redirect('personnel_login')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('personnel_login')

@login_required(login_url='personnel_login')
def view_attendance_history(request):
    personnel = Personnel.objects.get(user=request.user)
    
    # Get recent activities
    recent_activities = StudentActivity.objects.filter(
        personnel=personnel
    ).select_related('student').order_by('-date')[:10]
    
    context = {
        'personnel': personnel,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'personnel/attendance_history.html', context)