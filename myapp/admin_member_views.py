from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import FlightGroup, Personnel
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse


def personnel_list(request):
    personnel = Personnel.objects.all()
    flight_groups = FlightGroup.objects.all()
    
    # Calculate counts for the cards
    active_count = Personnel.objects.filter(status='Active').count()
    male_count = Personnel.objects.filter(gender='Male').count()
    female_count = Personnel.objects.filter(gender='Female').count()
    
    # Add flight group statistics
    total_groups = flight_groups.count()
    
    return render(request, 'admin/admin_personnel_list.html', {
        'personnel': personnel,
        'flight_groups': flight_groups,
        'active_count': active_count,
        'male_count': male_count,
        'female_count': female_count,
        'total_groups': total_groups
    })

def add_personnel(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        position = request.POST['position']
        status = request.POST['status']
        student_id = request.POST['student_id']
        age = request.POST['age']
        gender = request.POST['gender']
        phone_number = request.POST['phone_number']
        profile_picture = request.FILES.get('profile_picture')
        flight_group_id = request.POST.get('flight_group')

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            flight_group = FlightGroup.objects.get(id=flight_group_id) if flight_group_id else None
            personnel = Personnel(
                user=user,
                first_name=first_name,
                last_name=last_name,
                position=position,
                status=status,
                student_id=student_id,
                age=age,
                gender=gender,
                phone_number=phone_number,
                profile_picture=profile_picture,
                flight_group=flight_group
            )
            personnel.save()
            messages.success(request, "Personnel added successfully.")
            return redirect('admin_personnel_list')
        except Exception as e:
            messages.error(request, f"Error adding personnel: {e}")
            return redirect('add_personnel')

    flight_groups = FlightGroup.objects.all()
    return render(request, 'admin/admin_personnel_list.html', {'flight_groups': flight_groups})


def edit_personnel(request, personnel_id):
    personnel = get_object_or_404(Personnel, id=personnel_id)

    if request.method == 'POST':
        # Update user information
        personnel.user.first_name = request.POST['first_name']
        personnel.user.last_name = request.POST['last_name']
        if request.POST.get('password'):
            personnel.user.set_password(request.POST['password'])
        personnel.user.save()

        # Update personnel information
        personnel.first_name = request.POST['first_name']
        personnel.last_name = request.POST['last_name']
        personnel.position = request.POST['position']
        personnel.status = request.POST['status']
        personnel.student_id = request.POST['student_id']
        personnel.age = request.POST['age']
        personnel.gender = request.POST['gender']
        personnel.phone_number = request.POST['phone_number']
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            personnel.profile_picture = request.FILES['profile_picture']
        
        flight_group_id = request.POST.get('flight_group')
        if flight_group_id:
            personnel.flight_group = FlightGroup.objects.get(id=flight_group_id)
        else:
            personnel.flight_group = None

        personnel.save()
        messages.success(request, "Personnel updated successfully.")
        return redirect('admin_personnel_list')

    flight_groups = FlightGroup.objects.all()
    return render(request, 'admin/admin_edit_personnel.html', 
                 {'personnel': personnel, 'flight_groups': flight_groups})


def delete_personnel(request, personnel_id):
    personnel = get_object_or_404(Personnel, id=personnel_id)
    personnel.user.delete()  # Deletes the associated user as well
    personnel.delete()
    messages.success(request, "Personnel deleted successfully.")
    return redirect('admin_personnel_list')

def bulk_delete_personnel(request):
    if request.method == 'POST':
        personnel_ids = request.POST.getlist('personnel_ids[]')
        try:
            personnel_list = Personnel.objects.filter(id__in=personnel_ids)
            for personnel in personnel_list:
                personnel.user.delete()  # This will also delete the personnel due to CASCADE
            return JsonResponse({'status': 'success', 'message': f'{len(personnel_ids)} personnel deleted successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# Add flight group management functions
def add_flight_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        try:
            FlightGroup.objects.create(name=name, description=description)
            messages.success(request, f'Flight group "{name}" created successfully.')
        except Exception as e:
            messages.error(request, f'Error creating flight group: {str(e)}')
    
    return redirect('admin_personnel_list')

def edit_flight_group(request, group_id):
    group = get_object_or_404(FlightGroup, id=group_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        try:
            group.name = name
            group.description = description
            group.save()
            messages.success(request, f'Flight group "{name}" updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating flight group: {str(e)}')
    
    return redirect('admin_personnel_list')

def delete_flight_group(request, group_id):
    group = get_object_or_404(FlightGroup, id=group_id)
    
    try:
        group_name = group.name
        group.delete()
        messages.success(request, f'Flight group "{group_name}" deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting flight group: {str(e)}')
    
    return redirect('admin_personnel_list')
