from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from myapp.models import Personnel, FlightGroup, UserProfile, StudentRecord
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache

def home(request):
    """View for the homepage"""
    stats = {
        'total_personnel': Personnel.objects.count(),
        'total_groups': FlightGroup.objects.count(),
    }
    return render(request, 'homepage/home.html', {'stats': stats})

@never_cache
def login_view(request):
    """View for the login page"""
    # Check if user is already logged in
    if request.user.is_authenticated:
        # Redirect based on user type
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            
            if user_profile.user_type == 'personnel':
                response = redirect('personnel_dashboard')
                # Add cache control headers
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            elif user_profile.user_type == 'student':
                response = redirect('student_dashboard')
                # Add cache control headers
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            else:
                response = redirect('home')
                # Add cache control headers
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
                
        except UserProfile.DoesNotExist:
            # If no profile exists, try to determine type from related models
            is_personnel = hasattr(request.user, 'personnel')
            is_student = StudentRecord.objects.filter(user=request.user).exists()
            
            if is_personnel:
                response = redirect('personnel_dashboard')
                # Add cache control headers
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            elif is_student:
                response = redirect('student_dashboard')
                # Add cache control headers
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            elif request.user.is_staff:
                response = redirect('admin_dashboard')
                # Add cache control headers
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            else:
                response = redirect('home')
                # Add cache control headers
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check if user is admin (superuser)
            if user.is_superuser:
                messages.info(request, 'Admin users should use the admin login page')
                logout(request)
                return redirect('login')
            
            # Determine user type and redirect accordingly
            try:
                user_profile = UserProfile.objects.get(user=user)
                
                if user_profile.user_type == 'personnel':
                    messages.success(request, f'Welcome back, {user.username}!')
                    response = redirect('personnel_dashboard')
                    # Add cache control headers
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                    
                elif user_profile.user_type == 'student':
                    messages.success(request, f'Welcome back, {user.username}!')
                    response = redirect('student_dashboard')
                    # Add cache control headers
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                    
                else:
                    # Fallback for unknown user types
                    messages.warning(request, 'User type not recognized')
                    response = redirect('home')
                    # Add cache control headers
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                    
            except UserProfile.DoesNotExist:
                # If no profile exists, try to determine type from related models
                is_personnel = hasattr(user, 'personnel')
                
                # Check if user is associated with a student record
                is_student = StudentRecord.objects.filter(user=user).exists()
                
                if is_personnel:
                    messages.success(request, f'Welcome back, {user.username}!')
                    response = redirect('personnel_dashboard')
                    # Add cache control headers
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                elif is_student:
                    messages.success(request, f'Welcome back, {user.username}!')
                    response = redirect('student_dashboard')
                    # Add cache control headers
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                else:
                    messages.warning(request, 'Your account is not properly configured')
                    logout(request)
                    return redirect('login')
        else:
            messages.error(request, 'Invalid username or password')
    
    # Add cache control headers to the login page response
    response = render(request, 'homepage/login.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
def logout_view(request):
    """View for logging out"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    response = redirect('home')
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
def admin_login(request):
    """Separate login view for administrators"""
    # Check if user is already logged in as admin
    if request.user.is_authenticated and request.user.is_staff:
        response = redirect('admin_dashboard')
        # Add cache control headers
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f'Welcome back, Administrator {user.username}!')
            response = redirect('admin_dashboard')
            # Add cache control headers
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        else:
            messages.error(request, 'Invalid admin credentials or insufficient permissions')
    
    # Add cache control headers to the admin login page response
    response = render(request, 'homepage/admin_login.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response