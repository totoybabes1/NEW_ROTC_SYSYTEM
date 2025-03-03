from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import FlightGroup

# Flight groups page (display and add new)
@login_required
def flight_groups(request):
    if request.method == 'POST':
        # Handling form submission to add a new flight group
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        # Create a new flight group in the database
        FlightGroup.objects.create(name=name, description=description)
        
        # Show success message and redirect to reload the page  
        messages.success(request, "Flight group added successfully!")
        return redirect('admin_flight_groups')  # Reload the page to show the newly added group

    # Get all flight groups from the database to display them
    flight_groups = FlightGroup.objects.all()
    
    # Render the combined template with the flight groups and the form
    return render(request, 'admin/admin_flight_groups.html', {'flight_groups': flight_groups})

# Edit Flight Group
@login_required
def edit_flight_group(request, group_id):
    group = get_object_or_404(FlightGroup, id=group_id)

    if request.method == 'POST':
        group.name = request.POST.get('name')
        group.description = request.POST.get('description')
        group.save()

        messages.success(request, "Flight group updated successfully!")
        return redirect('admin_flight_groups')

    return render(request, 'admin/admin_edit_flight_group.html', {'group': group})

# Delete Flight Group
@login_required
def delete_flight_group(request, group_id):
    group = get_object_or_404(FlightGroup, id=group_id)
    group.delete()
    messages.success(request, "Flight group deleted successfully!")
    return redirect('admin_flight_groups')
