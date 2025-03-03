from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Profile

@login_required
def admin_profile(request):
    # Get or create profile for the user
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            messages.success(request, 'Profile picture updated successfully.')
            return redirect('admin_profile')

        # Handle profile information update
        email = request.POST.get('email')
        bio = request.POST.get('bio')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Update email
        if email and email != request.user.email:
            request.user.email = email
            request.user.save()

        # Update bio
        if bio is not None:  # Allow empty bio
            profile.bio = bio
            profile.save()

        # Update password
        if new_password:
            if new_password == confirm_password:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password updated successfully. Please login again.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect('admin_profile')

        messages.success(request, 'Profile updated successfully.')
        return redirect('admin_profile')

    return render(request, 'admin/profile.html')