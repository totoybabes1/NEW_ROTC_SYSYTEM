from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Personnel, StudentRecord, PersonnelStudentAssignment, StudentSpecialCase

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
    
    # Get unassigned students with related special cases
    assigned_student_ids = assignments.values_list('student_id', flat=True)
    unassigned_students = StudentRecord.objects.exclude(
        id__in=assigned_student_ids
    ).select_related('special_case').order_by('name')
    
    # Get all assignments for the student assignment table
    all_assignments = PersonnelStudentAssignment.objects.select_related('student', 'personnel').all()
    
    # Get special cases with related student data and handler data
    special_cases = StudentSpecialCase.objects.select_related('student', 'handler').order_by(
        'student__name'
    ).all()
    
    context = {
        'personnel_list': personnel_list,
        'student_list': student_list,
        'personnel_assignments': personnel_assignments,
        'unassigned_students': unassigned_students,
        'unassigned_count': unassigned_students.count(),
        'total_students': student_list.count(),
        'total_personnel': personnel_list.count(),
        'total_assignments': assignments.count(),
        'all_assignments': all_assignments,
        'special_cases': special_cases,
    }
    
    return render(request, 'admin/admin_assigned_personnel.html', context)

@login_required
def auto_assign_students(request):
    """
    Automatically assign students to personnel based on gender, excluding special cases
    """
    if request.method == 'POST':
        try:
            # Get the maximum limit from the form
            max_limit = int(request.POST.get('max_limit', 50))
            
            # Get all personnel with gender assignments
            male_personnel = list(Personnel.objects.filter(gender_assignment='Male'))
            female_personnel = list(Personnel.objects.filter(gender_assignment='Female'))
            
            # IMPORTANT: This part excludes special cases from auto-assignment
            special_case_students = StudentSpecialCase.objects.values_list('student_id', flat=True)
            assigned_student_ids = PersonnelStudentAssignment.objects.values_list('student_id', flat=True)
            unassigned_students = StudentRecord.objects.exclude(
                id__in=list(assigned_student_ids) + list(special_case_students)
            )
            
            # Only non-special case students are assigned
            male_students = list(unassigned_students.filter(gender='M'))
            female_students = list(unassigned_students.filter(gender='F'))
            
            # Track assignments per personnel
            personnel_assignment_count = {}
            for personnel in male_personnel + female_personnel:
                # Initialize with current assignment count
                personnel_assignment_count[personnel.id] = PersonnelStudentAssignment.objects.filter(
                    personnel=personnel
                ).count()
            
            # Assign male students
            if male_personnel:
                for student in male_students:
                    # Find the male personnel with the fewest assignments
                    available_personnel = sorted(
                        [p for p in male_personnel if personnel_assignment_count.get(p.id, 0) < max_limit],
                        key=lambda p: personnel_assignment_count.get(p.id, 0)
                    )
                    
                    if available_personnel:
                        personnel = available_personnel[0]
                        PersonnelStudentAssignment.objects.create(
                            personnel=personnel,
                            student=student
                        )
                        # Increment the count
                        personnel_assignment_count[personnel.id] = personnel_assignment_count.get(personnel.id, 0) + 1
            
            # Assign female students
            if female_personnel:
                for student in female_students:
                    # Find the female personnel with the fewest assignments
                    available_personnel = sorted(
                        [p for p in female_personnel if personnel_assignment_count.get(p.id, 0) < max_limit],
                        key=lambda p: personnel_assignment_count.get(p.id, 0)
                    )
                    
                    if available_personnel:
                        personnel = available_personnel[0]
                        PersonnelStudentAssignment.objects.create(
                            personnel=personnel,
                            student=student
                        )
                        # Increment the count
                        personnel_assignment_count[personnel.id] = personnel_assignment_count.get(personnel.id, 0) + 1
            
            total_assigned = len(male_students) + len(female_students)
            messages.success(request, f'Successfully assigned {total_assigned} students to personnel based on gender, with a maximum of {max_limit} students per personnel.')
            
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
            
            # Create the assignment
            assignment = PersonnelStudentAssignment.objects.create(
                student=student,
                personnel=personnel
            )
            
            messages.success(request, f'Successfully assigned {student.name} to {personnel.first_name} {personnel.last_name}.')
            
        except StudentRecord.DoesNotExist:
            messages.error(request, 'Student not found.')
        except Personnel.DoesNotExist:
            messages.error(request, 'Personnel not found.')
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

@login_required
def handle_special_cases(request):
    """
    Handle special case assignments for students (band, office, other gender)
    """
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        case_type = request.POST.get('special_case_type')
        handler_id = request.POST.get('handler_id')
        notes = request.POST.get('notes', '')
        case_id = request.POST.get('case_id')  # For editing existing cases

        try:
            handler = None
            if handler_id:
                try:
                    handler = Personnel.objects.get(id=handler_id)
                except Personnel.DoesNotExist:
                    pass

            # If editing a single case
            if case_id:
                special_case = get_object_or_404(StudentSpecialCase, id=case_id)
                special_case.case_type = case_type
                special_case.handler = handler
                special_case.handler_name = handler.first_name + " " + handler.last_name if handler else ""
                special_case.notes = notes
                special_case.save()
                
                messages.success(request, f'Successfully updated special case for {special_case.student.name}')
                
            # If creating/updating multiple cases
            else:
                # Process each selected student
                for student_id in student_ids:
                    student = StudentRecord.objects.get(id=student_id)
                    
                    # Update or create special case
                    special_case, created = StudentSpecialCase.objects.update_or_create(
                        student=student,
                        defaults={
                            'case_type': case_type,
                            'handler': handler,
                            'handler_name': handler.first_name + " " + handler.last_name if handler else "",
                            'notes': notes
                        }
                    )

                    # Remove any existing assignment if present
                    PersonnelStudentAssignment.objects.filter(student=student).delete()

                action = 'Updated' if not created else 'Created'
                messages.success(
                    request, 
                    f'Successfully {action.lower()} special case(s) for {len(student_ids)} student(s)'
                )

        except Exception as e:
            messages.error(request, f'Error processing special cases: {str(e)}')

    return redirect('assigned_personnel_list')

@login_required
def remove_special_case(request, case_id):
    """
    Remove a student's special case status
    """
    try:
        special_case = get_object_or_404(StudentSpecialCase, id=case_id)
        student_name = special_case.student.name
        case_type = special_case.get_case_type_display()
        special_case.delete()
        messages.success(request, f'Removed {case_type} status from {student_name}')
    except Exception as e:
        messages.error(request, f'Error removing special case: {str(e)}')
    
    return redirect('assigned_personnel_list')

@login_required
def bulk_remove_special_cases(request):
    """
    Remove multiple special cases at once
    """
    if request.method == 'POST':
        case_ids = request.POST.get('case_ids', '').split(',')
        try:
            cases = StudentSpecialCase.objects.filter(id__in=case_ids)
            count = cases.count()
            cases.delete()
            messages.success(request, f'Successfully removed {count} special case(s).')
        except Exception as e:
            messages.error(request, f'Error removing special cases: {str(e)}')
    
    return redirect('assigned_personnel_list')