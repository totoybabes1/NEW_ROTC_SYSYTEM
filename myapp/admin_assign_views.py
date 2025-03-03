from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Personnel

def assign_gender(request):
    personnel_list = Personnel.objects.all()
    
    if request.method == 'POST':
        # Get all form data
        for key, value in request.POST.items():
            if key.startswith('gender_assignment_'):
                personnel_id = key.replace('gender_assignment_', '')
                try:
                    person = Personnel.objects.get(id=personnel_id)
                    person.gender_assignment = value
                    person.save()
                except Personnel.DoesNotExist:
                    continue
        
        messages.success(request, 'Gender assignments updated successfully.')
        return redirect('admin_personnel_list')
    
    return render(request, 'admin/admin_assign_gender.html', {'personnel_list': personnel_list})