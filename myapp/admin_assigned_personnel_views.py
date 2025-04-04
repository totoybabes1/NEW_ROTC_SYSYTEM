from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Personnel, StudentRecord, PersonnelStudentAssignment, StudentSpecialCase, SemesterYear
from django.db.models import Q

@login_required
def assigned_personnel_list(request):
    """
    Display and manage personnel-student assignments
    """
    # Get all personnel and students
    personnel_list = Personnel.objects.all()
    
    # Modify the semester years query to only get active semesters
    semester_years = SemesterYear.objects.filter(is_active=True).order_by('-academic_year', 'semester')
    
    # Get students from active semesters only
    active_semester_ids = semester_years.values_list('id', flat=True)
    student_list = StudentRecord.objects.filter(
        Q(semester_year__in=active_semester_ids) | Q(semester_year__isnull=True)
    )
    
    # Update assignments to only show students from active semesters
    assignments = PersonnelStudentAssignment.objects.filter(
        student__semester_year__in=active_semester_ids
    )
    
    # Update unassigned students query
    assigned_student_ids = assignments.values_list('student_id', flat=True)
    unassigned_students = student_list.exclude(
        id__in=assigned_student_ids
    ).order_by('name')
    
    # Create a dictionary to store students assigned to each personnel
    personnel_assignments = {}
    for personnel in personnel_list:
        personnel_assignments[personnel.id] = []
    
    # Populate the dictionary with existing assignments
    for assignment in assignments:
        if assignment.personnel_id in personnel_assignments:
            personnel_assignments[assignment.personnel_id].append(assignment.student)
    
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
        'all_assignments': assignments,  # Updated to filtered assignments
        'special_cases': special_cases,
        'semester_years': semester_years,  # Now only contains active semesters
    }
    
    return render(request, 'admin/admin_assigned_personnel.html', context)

@login_required
def auto_assign_students(request):
    """
    Automatically assign students to personnel based on gender, excluding special cases
    """
    if request.method == 'POST':
        try:
            max_limit = int(request.POST.get('max_limit', 50))
            
            # Get active semester IDs
            active_semester_ids = SemesterYear.objects.filter(is_active=True).values_list('id', flat=True)
            
            # Get IDs of personnel who are handling special cases
            special_case_handler_ids = StudentSpecialCase.objects.values_list('handler_id', flat=True).distinct()
            
            # Get all personnel with gender assignments, excluding special case handlers
            male_personnel = list(Personnel.objects.filter(gender_assignment='Male')
                                .exclude(id__in=special_case_handler_ids))
            female_personnel = list(Personnel.objects.filter(gender_assignment='Female')
                                .exclude(id__in=special_case_handler_ids))
            
            # Get IDs of students with special cases
            special_case_ids = StudentSpecialCase.objects.values_list('student_id', flat=True)
            
            # Get currently assigned students
            assigned_student_ids = PersonnelStudentAssignment.objects.values_list('student_id', flat=True)
            
            # Get unassigned students excluding special cases and only from active semesters
            unassigned_students = StudentRecord.objects.filter(
                Q(semester_year__in=active_semester_ids) | Q(semester_year__isnull=True)
            ).exclude(
                Q(id__in=assigned_student_ids) | Q(id__in=special_case_ids)
            )
            
            # Split by gender
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
    Reset all student assignments
    """
    if request.method == 'POST':
        try:
            # Get active semester IDs
            active_semester_ids = SemesterYear.objects.filter(is_active=True).values_list('id', flat=True)
            
            # Check if we have any active semesters
            if not active_semester_ids:
                messages.warning(request, 'No active semesters found. No assignments were reset.')
                return redirect('assigned_personnel_list')
            
            # Only delete assignments for students in active semesters
            # Use a more inclusive query that handles null semester_year values
            deleted_count, _ = PersonnelStudentAssignment.objects.filter(
                Q(student__semester_year__in=active_semester_ids) | 
                Q(student__semester_year__isnull=True)
            ).delete()
            
            if deleted_count > 0:
                messages.success(request, f'Successfully reset {deleted_count} student assignments.')
            else:
                messages.info(request, 'No assignments were found to reset.')
                
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

@login_required
def manual_special_case_assignment(request):
    """
    Manually assign multiple special case students to a specific personnel
    These assignments will be excluded from auto-assignment process
    """
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids[]')  # Note the [] for multiple select
        personnel_id = request.POST.get('personnel_id')
        case_type = request.POST.get('case_type')
        notes = request.POST.get('notes', '')

        try:
            personnel = Personnel.objects.get(id=personnel_id)
            success_count = 0

            for student_id in student_ids:
                try:
                    student = StudentRecord.objects.get(id=student_id)

                    # Create or update the special case
                    special_case, created = StudentSpecialCase.objects.update_or_create(
                        student=student,
                        defaults={
                            'case_type': case_type,
                            'handler': personnel,
                            'handler_name': f"{personnel.first_name} {personnel.last_name}",
                            'notes': notes
                        }
                    )

                    # Create the manual assignment
                    PersonnelStudentAssignment.objects.update_or_create(
                        student=student,
                        defaults={
                            'personnel': personnel,
                        }
                    )
                    
                    success_count += 1

                except StudentRecord.DoesNotExist:
                    messages.warning(request, f'Student with ID {student_id} not found.')
                except Exception as e:
                    messages.warning(request, f'Error processing student {student_id}: {str(e)}')

            if success_count > 0:
                messages.success(
                    request,
                    f'Successfully created special case assignments for {success_count} student(s) to {personnel.first_name} {personnel.last_name}'
                )

        except Personnel.DoesNotExist:
            messages.error(request, 'Personnel not found.')
        except Exception as e:
            messages.error(request, f'Error creating special case assignments: {str(e)}')

    return redirect('assigned_personnel_list')