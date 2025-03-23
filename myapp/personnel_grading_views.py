from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import Personnel, StudentRecord, PersonnelStudentAssignment, StudentActivity, StudentGrade
import json

@login_required
def student_grading(request, student_id):
    """View for grading a specific student"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        student = get_object_or_404(StudentRecord, id=student_id)
        
        # Verify this student is assigned to this personnel
        if not PersonnelStudentAssignment.objects.filter(personnel=personnel, student=student).exists():
            messages.error(request, "This student is not assigned to you.")
            return redirect('view_assigned_students')
        
        # Get student activities
        activities = StudentActivity.objects.filter(
            student=student,
            personnel=personnel
        ).order_by('-date')
        
        # Get or create student grade
        grade, created = StudentGrade.objects.get_or_create(
            student=student,
            personnel=personnel
        )
        
        context = {
            'personnel': personnel,
            'student': student,
            'activities': activities,
            'grade': grade,
            'today': timezone.now().date()
        }
        
        return render(request, 'personnel/grading.html', context)
    except Personnel.DoesNotExist:
        messages.error(request, "Personnel profile not found.")
        return redirect('personnel_login')

@login_required
def add_student_activity(request, student_id):
    """Add a new activity for a student"""
    if request.method == 'POST':
        try:
            personnel = Personnel.objects.get(user=request.user)
            student = get_object_or_404(StudentRecord, id=student_id)
            
            # Verify this student is assigned to this personnel
            if not PersonnelStudentAssignment.objects.filter(personnel=personnel, student=student).exists():
                messages.error(request, "This student is not assigned to you.")
                return redirect('view_assigned_students')
            
            # Create new activity
            activity = StudentActivity.objects.create(
                student=student,
                personnel=personnel,
                sf=request.POST.get('sf'),
                date=request.POST.get('date'),
                cadet_sign=request.POST.get('cadet_sign', ''),
                activity_description=request.POST.get('activity_description'),
                merits=request.POST.get('merits', 0),
                demerits=request.POST.get('demerits', 0),
                flight_leader_sign=request.POST.get('flight_leader_sign', ''),
                remarks=request.POST.get('remarks', '')
            )
            
            messages.success(request, "Activity added successfully.")
            return redirect('student_grading', student_id=student_id)
        except Exception as e:
            messages.error(request, f"Error adding activity: {str(e)}")
            return redirect('student_grading', student_id=student_id)
    
    return redirect('student_grading', student_id=student_id)

@login_required
def edit_student_activity(request, activity_id):
    """Edit an existing student activity"""
    activity = get_object_or_404(StudentActivity, id=activity_id)
    student_id = activity.student.id
    
    # Verify this activity belongs to the logged-in personnel
    if activity.personnel.user != request.user:
        messages.error(request, "You don't have permission to edit this activity.")
        return redirect('student_grading', student_id=student_id)
    
    if request.method == 'POST':
        try:
            # Update activity fields
            activity.sf = request.POST.get('sf')
            activity.date = request.POST.get('date')
            activity.cadet_sign = request.POST.get('cadet_sign', '')
            activity.activity_description = request.POST.get('activity_description')
            activity.merits = request.POST.get('merits', 0)
            activity.demerits = request.POST.get('demerits', 0)
            activity.flight_leader_sign = request.POST.get('flight_leader_sign', '')
            activity.remarks = request.POST.get('remarks', '')
            activity.save()
            
            messages.success(request, "Activity updated successfully.")
            return redirect('student_grading', student_id=student_id)
        except Exception as e:
            messages.error(request, f"Error updating activity: {str(e)}")
            return redirect('student_grading', student_id=student_id)
    
    return redirect('student_grading', student_id=student_id)

@login_required
def delete_student_activity(request, activity_id):
    """Delete a student activity"""
    activity = get_object_or_404(StudentActivity, id=activity_id)
    student_id = activity.student.id
    
    # Verify this activity belongs to the logged-in personnel
    if activity.personnel.user != request.user:
        return JsonResponse({
            'success': False,
            'message': "You don't have permission to delete this activity."
        })
    
    try:
        activity.delete()
        return JsonResponse({
            'success': True,
            'message': "Activity deleted successfully."
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f"Error deleting activity: {str(e)}"
        })

@login_required
def get_student_activity(request, activity_id):
    """Get details of a student activity"""
    activity = get_object_or_404(StudentActivity, id=activity_id)
    
    # Verify this activity belongs to the logged-in personnel
    if activity.personnel.user != request.user:
        return JsonResponse({
            'success': False,
            'message': "You don't have permission to view this activity."
        })
    
    return JsonResponse({
        'success': True,
        'activity': {
            'id': activity.id,
            'sf': activity.sf,
            'date': activity.date.strftime('%Y-%m-%d'),
            'cadet_sign': activity.cadet_sign,
            'activity_description': activity.activity_description,
            'merits': activity.merits,
            'demerits': activity.demerits,
            'flight_leader_sign': activity.flight_leader_sign,
            'remarks': activity.remarks
        }
    })

@login_required
def update_student_grade(request, student_id):
    """Update a student's grade"""
    if request.method == 'POST':
        try:
            personnel = Personnel.objects.get(user=request.user)
            student = get_object_or_404(StudentRecord, id=student_id)
            
            # Get form data
            num_periods = request.POST.get('num_periods', 0)
            num_merits = request.POST.get('num_merits', 0)
            num_demerits = request.POST.get('num_demerits', 0)
            subject_score = request.POST.get('subject_score', 0)
            
            # Get calculated scores
            attendance_score = request.POST.get('attendance_score', 0)
            military_score = request.POST.get('military_score', 0)
            proficiency_score = request.POST.get('proficiency_score', 0)
            total_grade = request.POST.get('total_grade', 0)
            
            # Update or create grade record
            grade, created = StudentGrade.objects.update_or_create(
                student=student,
                personnel=personnel,
                defaults={
                    'num_periods': num_periods,
                    'num_merits': num_merits,
                    'num_demerits': num_demerits,
                    'subject_score': subject_score,
                    'attendance_score': attendance_score,
                    'military_score': military_score,
                    'proficiency_score': proficiency_score,
                    'total_grade': total_grade,
                }
            )
            
            messages.success(request, 'Student grade updated successfully.')
            return redirect('student_grading', student_id=student_id)
            
        except Exception as e:
            messages.error(request, f'Error updating grade: {str(e)}')
            return redirect('student_grading', student_id=student_id)
    
    return redirect('student_grading', student_id=student_id)

@login_required
def view_student_grades(request):
    """View grades for all assigned students"""
    try:
        personnel = Personnel.objects.get(user=request.user)
        assignments = PersonnelStudentAssignment.objects.filter(
            personnel=personnel
        ).select_related('student')
        
        # Get grades for all assigned students
        students_with_grades = []
        for assignment in assignments:
            grade, created = StudentGrade.objects.get_or_create(
                student=assignment.student,
                personnel=personnel
            )
            
            students_with_grades.append({
                'student': assignment.student,
                'grade': grade
            })
        
        context = {
            'personnel': personnel,
            'students_with_grades': students_with_grades
        }
        
        return render(request, 'personnel/student_grades.html', context)
    except Personnel.DoesNotExist:
        messages.error(request, "Personnel profile not found.")
        return redirect('personnel_login')