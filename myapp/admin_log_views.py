from django.shortcuts import render
from .models import UserActivity
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    UserActivity.objects.create(user=user, activity_type='login')

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    UserActivity.objects.create(user=user, activity_type='logout')

def admin_dashboard(request):
    if request.user.is_staff:
        recent_activities = UserActivity.objects.order_by('-timestamp')[:10]  # Fetch the latest 10 activities
        return render(request, 'admin/admin_dashboard.html', {'recent_activities': recent_activities})
    else:
        return render(request, 'admin/admin_dashboard.html', {'error': 'You do not have permission to access this page.'}) 