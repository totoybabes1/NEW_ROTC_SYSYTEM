from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from myapp.models import Personnel, FlightGroup, UploadFiles, Profile
from django.http import JsonResponse
from datetime import datetime

def home(request):
    stats = {
        'total_personnel': Personnel.objects.count(),
        'total_groups': FlightGroup.objects.count(),
        'total_files': UploadFiles.objects.count(),
    }
    return render(request, 'admin/admin_home.html', {'stats': stats})

@login_required(login_url='login')
def admin_dashboard(request):
    # Get statistics
    stats = {
        'total_personnel': Personnel.objects.count(),
        'total_groups': FlightGroup.objects.count(),
        'total_files': UploadFiles.objects.count(),
        'recent_uploads': UploadFiles.objects.order_by('-created_at')[:5].count(),
        
        # Gender statistics
        'gender_male': Personnel.objects.filter(gender_assignment='Male').count(),
        'gender_female': Personnel.objects.filter(gender_assignment='Female').count(),
        'gender_nonbinary': Personnel.objects.filter(gender_assignment='Non-binary').count(),
        'gender_other': Personnel.objects.filter(gender_assignment='Other').count(),
    }

    # Get flight group data for chart
    flight_groups = FlightGroup.objects.all()
    group_names = [group.name for group in flight_groups]
    group_members = [Personnel.objects.filter(flight_group=group).count() for group in flight_groups]

    # Get recent activities
    recent_activities = []
    
    # Get recent personnel (last 5)
    for person in Personnel.objects.order_by('-date_joined')[:5]:
        recent_activities.append({
            'type': 'user',
            'description': f'New personnel added: {person.first_name} {person.last_name}',
            'timestamp': person.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            'user': 'Admin'
        })

    # Get recent uploads (last 5)
    for upload in UploadFiles.objects.order_by('-created_at')[:5]:
        recent_activities.append({
            'type': 'upload',
            'description': f'New file uploaded: {upload.table_name}',
            'timestamp': upload.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user': 'Admin'
        })

    # Get profile activities
    profile_activities = []
    profiles = Profile.objects.all().order_by('-last_activity')[:10]
    for profile in profiles:
        if profile.activity_log:
            # Get the last 5 activities for each profile
            recent_logs = profile.activity_log[-5:]
            for log in recent_logs:
                profile_activities.append({
                    'user': profile.user.username,
                    'action': log['action'],
                    'timestamp': datetime.fromisoformat(log['timestamp'])
                })
    
    # Sort activities by timestamp
    profile_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    context = {
        'stats': stats,
        'group_names': group_names,
        'group_members': group_members,
        'recent_activities': recent_activities,
        'profile_activities': profile_activities[:10]  # Get the 10 most recent activities
    }

    return render(request, 'admin/admin_dashboard.html', context)

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'admin/admin_login.html')

def admin_logout(request):
    logout(request)
    return redirect('home')  # Changed to redirect to home instead of login

@login_required(login_url='login')
def get_activities(request):
    page = request.GET.get('page', 1)
    filter_type = request.GET.get('filter', 'all')
    
    # Base queryset for activities
    activities = []
    
    # Add personnel activities
    personnel_qs = Personnel.objects.order_by('-date_joined')
    if filter_type in ['all', 'user']:
        for person in personnel_qs:
            activities.append({
                'type': 'user',
                'description': f'New personnel added: {person.first_name} {person.last_name}',
                'user': request.user.username,
                'category': 'Personnel',
                'timestamp': person.date_joined.isoformat(),
            })

    # Add upload activities
    upload_qs = UploadFiles.objects.order_by('-created_at')
    if filter_type in ['all', 'upload']:
        for upload in upload_qs:
            activities.append({
                'type': 'upload',
                'description': f'New file uploaded: {upload.table_name}',
                'user': request.user.username,
                'category': 'Upload',
                'timestamp': upload.created_at.isoformat(),
                'fileName': upload.table_name,
                'fileSize': upload.file_size,
            })

    # Add group activities
    group_qs = FlightGroup.objects.order_by('-created_at')
    if filter_type in ['all', 'group']:
        for group in group_qs:
            member_count = Personnel.objects.filter(flight_group=group).count()
            activities.append({
                'type': 'group',
                'description': f'Flight group updated: {group.name}',
                'user': request.user.username,
                'category': 'Groups',
                'timestamp': group.created_at.isoformat(),
                'memberCount': member_count,
            })

    # Sort activities by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Paginate activities
    page_size = 10
    start_idx = (int(page) - 1) * page_size
    end_idx = start_idx + page_size
    
    return JsonResponse({
        'activities': activities[start_idx:end_idx],
        'hasMore': end_idx < len(activities)
    })