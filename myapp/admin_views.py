from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from myapp.models import Personnel, FlightGroup, Profile, StudentRecord, UserActivity, PersonnelStudentAssignment, EventFlightGroup
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta


def home(request):
    stats = {
        'total_personnel': Personnel.objects.count(),
        'total_groups': FlightGroup.objects.count(),
    }
    return render(request, 'admin/admin_home.html', {'stats': stats})

@login_required(login_url='login')
def admin_dashboard(request):
    # Get current statistics
    
    # Get assignment statistics
    total_students = StudentRecord.objects.count()
    assigned_students = PersonnelStudentAssignment.objects.count()
    unassigned_students = total_students - assigned_students
    
    current_stats = {
        'total_personnel': Personnel.objects.count(),
        'total_groups': FlightGroup.objects.count(),
        
        # Add student assignment statistics
        'total_students': total_students,
        'assigned_students': assigned_students,
        'unassigned_students': unassigned_students,
        
        # Previous week's numbers for comparison
        'previous_total_personnel': Personnel.objects.filter(
            date_joined__lt=timezone.now() - timedelta(days=7)
        ).count(),
        'previous_total_groups': FlightGroup.objects.all().count(),
        
        # Gender statistics
        'gender_male': Personnel.objects.filter(gender='Male').count(),
        'gender_female': Personnel.objects.filter(gender='Female').count(),
        'gender_nonbinary': Personnel.objects.filter(gender_assignment='Non-binary').count(),
        'gender_other': Personnel.objects.filter(gender_assignment='Other').count(),
        
        # Student records statistics
        'total_students': StudentRecord.objects.count(),
        
        # User activity statistics
        'total_activities': UserActivity.objects.count(),
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
                    'timestamp': timezone.localtime(datetime.fromisoformat(log['timestamp']))
                })
    
    # Sort activities by timestamp
    profile_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    context = {
        'stats': current_stats,
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

@login_required
def get_quick_stats(request):
    total_personnel = Personnel.objects.count()
    active_personnel = Personnel.objects.filter(status='Active').count()
    personnel_with_groups = Personnel.objects.exclude(flight_group=None).count()
    
    active_percentage = (active_personnel / total_personnel * 100) if total_personnel > 0 else 0
    assigned_percentage = (personnel_with_groups / total_personnel * 100) if total_personnel > 0 else 0
    
    return JsonResponse({
        'active_percentage': round(active_percentage, 1),
        'assigned_percentage': round(assigned_percentage, 1)
    })

@login_required
def get_detailed_stats(request):
    """
    API endpoint to get detailed statistics for dashboard charts
    """
    # Student gender distribution
    male_students = StudentRecord.objects.filter(gender='M').count()
    female_students = StudentRecord.objects.filter(gender='F').count()
    
    # Personnel status distribution
    active_personnel = Personnel.objects.filter(status='Active').count()
    inactive_personnel = Personnel.objects.filter(status='Inactive').count()
    
    # Student year level distribution
    year_distribution = {}
    for year in range(1, 6):
        year_distribution[f'Year {year}'] = StudentRecord.objects.filter(year=year).count()
    
    # Student assignment statistics by gender
    male_personnel_assignments = PersonnelStudentAssignment.objects.filter(
        personnel__gender='Male'
    ).count()
    female_personnel_assignments = PersonnelStudentAssignment.objects.filter(
        personnel__gender='Female'
    ).count()
    
    # User activity over time (last 7 days)
    activity_data = []
    for i in range(7, 0, -1):
        date = timezone.now().date() - timedelta(days=i)
        next_date = date + timedelta(days=1)
        logins = UserActivity.objects.filter(
            activity_type='login',
            timestamp__gte=date,
            timestamp__lt=next_date
        ).count()
        activity_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'logins': logins
        })
    
    # Flight group size comparison
    flight_groups = FlightGroup.objects.all()
    group_data = []
    for group in flight_groups:
        group_data.append({
            'name': group.name,
            'personnel_count': Personnel.objects.filter(flight_group=group).count(),
            'event_count': EventFlightGroup.objects.filter(flight_group=group).count()
        })
    
    return JsonResponse({
        'student_gender': {
            'labels': ['Male', 'Female'],
            'data': [male_students, female_students]
        },
        'personnel_status': {
            'labels': ['Active', 'Inactive'],
            'data': [active_personnel, inactive_personnel]
        },
        'year_distribution': {
            'labels': list(year_distribution.keys()),
            'data': list(year_distribution.values())
        },
        'assignments_by_gender': {
            'labels': ['Male Personnel', 'Female Personnel'],
            'data': [male_personnel_assignments, female_personnel_assignments]
        },
        'activity_over_time': activity_data,
        'flight_groups': group_data
    })