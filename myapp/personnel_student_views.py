from pyexpat.errors import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Personnel, PersonnelStudentAssignment, StudentRecord
from django.db.models import Count



@login_required
def view_assigned_students(request):
    """View students assigned to the logged-in personnel"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        assignments = PersonnelStudentAssignment.objects.filter(personnel=personnel)
        
        # Get statistics
        total_students = assignments.count()
        
        # Group students by course
        students_by_course = {}
        for assignment in assignments:
            course = assignment.student.course
            if course not in students_by_course:
                students_by_course[course] = []
            students_by_course[course].append(assignment.student)
        
        # Get all assigned students
        assigned_students = [assignment.student for assignment in assignments]
        
        context = {
            'personnel': personnel,
            'assignments': assignments,
            'assigned_students': assigned_students,
            'total_students': total_students,
            'students_by_course': students_by_course,
        }
        
        return render(request, 'personnel/students_assigned.html', context)
    except Personnel.DoesNotExist:
        messages.error(request, "Personnel profile not found.")
        return redirect('personnel_login')


@login_required
def get_student_details(request, student_id):
    """API endpoint to get student details for modal"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        assignment = get_object_or_404(
            PersonnelStudentAssignment,
            personnel=personnel,
            student_id=student_id
        )
        student = assignment.student
        
        data = {
            'success': True,
            'student': {
                'id': student.id,
                'student_no': student.student_no,
                'name': student.name,
                'course': student.course,
                'year': student.year,
                'gender': student.gender,
                'status': student.status,
                'assigned_date': assignment.assigned_date.strftime('%B %d, %Y'),
            }
        }
        return JsonResponse(data)
    except (Personnel.DoesNotExist, PersonnelStudentAssignment.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Student not found'})

@login_required
def filter_students(request):
    """API endpoint to filter students"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        assignments = PersonnelStudentAssignment.objects.filter(personnel=personnel).select_related('student')
        
        # Get filter parameters
        course = request.GET.get('course')
        year = request.GET.get('year')
        gender = request.GET.get('gender')
        status = request.GET.get('status')
        search = request.GET.get('search')
        
        # Apply filters
        if course:
            assignments = assignments.filter(student__course=course)
        if year:
            assignments = assignments.filter(student__year=year)
        if gender:
            assignments = assignments.filter(student__gender=gender)
        if status:
            assignments = assignments.filter(student__status=status)
        if search:
            assignments = assignments.filter(
                student__name__icontains=search
            ) | assignments.filter(
                student__student_no__icontains=search
            )
        
        # Prepare data for response
        students_data = [{
            'id': assignment.student.id,
            'student_no': assignment.student.student_no,
            'name': assignment.student.name,
            'course': assignment.student.course,
            'year': assignment.student.year,
            'gender': assignment.student.gender,
            'status': assignment.student.status,
            'assigned_date': assignment.assigned_date.strftime('%B %d, %Y'),
        } for assignment in assignments]
        
        return JsonResponse({
            'success': True,
            'students': students_data
        })
    except Personnel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Personnel not found'})