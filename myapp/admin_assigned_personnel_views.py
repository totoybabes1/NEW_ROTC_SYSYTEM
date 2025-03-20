from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Personnel, StudentRecord, PersonnelStudentAssignment

@login_required
def assigned_personnel_list(request):
    """
    Display and manage personnel-student assignments
    """
    # Get all personnel and students
    personnel_list = Personnel.objects.all()
    student_list = StudentRecord.objects.all()
    
    # Get existing assignments
    assignments = PersonnelStudentAssignment.objects.all()
    
    # Create a dictionary to store students assigned to each personnel
    personnel_assignments = {}
    for personnel in personnel_list:
        personnel_assignments[personnel.id] = []
    
    # Populate the dictionary with existing assignments
    for assignment in assignments:
        if assignment.personnel_id in personnel_assignments:
            personnel_assignments[assignment.personnel_id].append(assignment.student)
    
    # Count unassigned students
    assigned_student_ids = assignments.values_list('student_id', flat=True)
    unassigned_students = StudentRecord.objects.exclude(id__in=assigned_student_ids)
    
    context = {
        'personnel_list': personnel_list,
        'student_list': student_list,
        'personnel_assignments': personnel_assignments,
        'unassigned_students': unassigned_students,
        'unassigned_count': unassigned_students.count(),
        'total_students': student_list.count(),
        'total_personnel': personnel_list.count(),
        'total_assignments': assignments.count()
    }
    
    return render(request, 'admin/admin_assigned_personnel.html', context)

@login_required
def auto_assign_students(request):
    """
    Automatically assign students to personnel based on gender
    """
    if request.method == 'POST':
        try:
            # Clear existing assignments if requested
            if request.POST.get('clear_existing') == 'true':
                PersonnelStudentAssignment.objects.all().delete()
                messages.success(request, 'Existing assignments cleared.')
            
            # Get all personnel with gender assignments
            male_personnel = Personnel.objects.filter(gender='Male')
            female_personnel = Personnel.objects.filter(gender='Female')
            
            # Get all unassigned students
            assigned_student_ids = PersonnelStudentAssignment.objects.values_list('student_id', flat=True)
            unassigned_students = StudentRecord.objects.exclude(id__in=assigned_student_ids)
            
            # Separate students by gender
            male_students = unassigned_students.filter(gender='M')
            female_students = unassigned_students.filter(gender='F')
            
            # Count for load balancing
            male_personnel_count = male_personnel.count()
            female_personnel_count = female_personnel.count()
            
            # Assign male students
            if male_personnel_count > 0:
                for i, student in enumerate(male_students):
                    # Distribute evenly among male personnel
                    personnel = male_personnel[i % male_personnel_count]
                    PersonnelStudentAssignment.objects.create(
                        personnel=personnel,
                        student=student
                    )
            
            # Assign female students
            if female_personnel_count > 0:
                for i, student in enumerate(female_students):
                    # Distribute evenly among female personnel
                    personnel = female_personnel[i % female_personnel_count]
                    PersonnelStudentAssignment.objects.create(
                        personnel=personnel,
                        student=student
                    )
            
            total_assigned = male_students.count() + female_students.count()
            messages.success(request, f'Successfully assigned {total_assigned} students to personnel based on gender.')
            
        except Exception as e:
            messages.error(request, f'Error assigning students: {str(e)}')
        
    return redirect('assigned_personnel_list')

@login_required
def manual_assign_student(request):
    """
    Manually assign a student to a personnel
    """
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        personnel_id = request.POST.get('personnel_id')
        
        try:
            student = StudentRecord.objects.get(id=student_id)
            personnel = Personnel.objects.get(id=personnel_id)
            
            # Check if student is already assigned
            existing_assignment = PersonnelStudentAssignment.objects.filter(student=student).first()
            if existing_assignment:
                # Update existing assignment
                existing_assignment.personnel = personnel
                existing_assignment.save()
                messages.success(request, f'Updated assignment for {student.name}.')
            else:
                # Create new assignment
                PersonnelStudentAssignment.objects.create(
                    personnel=personnel,
                    student=student
                )
                messages.success(request, f'Assigned {student.name} to {personnel.first_name} {personnel.last_name}.')
                
        except Exception as e:
            messages.error(request, f'Error assigning student: {str(e)}')
    
    return redirect('assigned_personnel_list')

@login_required
def remove_student_assignment(request, assignment_id):
    """
    Remove a student assignment
    """
    try:
        assignment = PersonnelStudentAssignment.objects.get(id=assignment_id)
        student_name = assignment.student.name
        personnel_name = f"{assignment.personnel.first_name} {assignment.personnel.last_name}"
        assignment.delete()
        messages.success(request, f'Removed assignment of {student_name} from {personnel_name}.')
    except PersonnelStudentAssignment.DoesNotExist:
        messages.error(request, 'Assignment not found.')
    except Exception as e:
        messages.error(request, f'Error removing assignment: {str(e)}')
    
    return redirect('assigned_personnel_list')

@login_required
def reassign_student(request):
    """
    Reassign a student from one personnel to another
    """
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        new_personnel_id = request.POST.get('new_personnel_id')
        
        try:
            student = StudentRecord.objects.get(id=student_id)
            new_personnel = Personnel.objects.get(id=new_personnel_id)
            
            # Get the current assignment
            current_assignment = PersonnelStudentAssignment.objects.get(student=student)
            old_personnel = current_assignment.personnel
            
            # Update the assignment
            current_assignment.personnel = new_personnel
            current_assignment.save()
            
            messages.success(request, f'Successfully reassigned {student.name} from {old_personnel.first_name} {old_personnel.last_name} to {new_personnel.first_name} {new_personnel.last_name}.')
            
        except StudentRecord.DoesNotExist:
            messages.error(request, 'Student not found.')
        except Personnel.DoesNotExist:
            messages.error(request, 'Personnel not found.')
        except PersonnelStudentAssignment.DoesNotExist:
            messages.error(request, 'Assignment not found.')
        except Exception as e:
            messages.error(request, f'Error reassigning student: {str(e)}')
    
    return redirect('assigned_personnel_list')

@login_required
def reset_all_assignments(request):
    """
    Reset all student assignments by deleting all PersonnelStudentAssignment records
    """
    if request.method == 'POST':
        try:
            # Count assignments before deletion for the success message
            assignment_count = PersonnelStudentAssignment.objects.count()
            
            # Delete all assignment records
            PersonnelStudentAssignment.objects.all().delete()
            
            messages.success(request, f'Successfully reset all assignments. {assignment_count} assignments were cleared.')
        except Exception as e:
            messages.error(request, f'Error resetting assignments: {str(e)}')
    
    return redirect('assigned_personnel_list')