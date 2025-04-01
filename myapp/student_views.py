from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StudentRecord, StudentAttendance, StudentGrade, StudentActivity
from django.db.models import Sum

def student_login(request):
    if request.method == 'POST':
        student_no = request.POST.get('student_no')
        password = request.POST.get('password')
        
        # You'll need to implement proper authentication here
        # This is a basic example
        try:
            student = StudentRecord.objects.get(student_no=student_no)
            user = authenticate(request, username=student_no, password=password)
            if user is not None:
                login(request, user)
                return redirect('student_dashboard')
            else:
                messages.error(request, 'Invalid credentials')
        except StudentRecord.DoesNotExist:
            messages.error(request, 'Student not found')
            
    return render(request, 'student/login.html')

@login_required
def student_dashboard(request):
    try:
        # Get the student record based on the logged-in user's username (student number)
        student = StudentRecord.objects.get(student_no=request.user.username)
        
        # Get attendance records
        attendance = StudentAttendance.objects.filter(student=student).order_by('-date')[:5]
        
        # Get latest grades
        grades = StudentGrade.objects.filter(student=student).order_by('-date_computed')[:1]
        
        # Get merits and demerits
        activities = StudentActivity.objects.filter(student=student)
        total_merits = activities.aggregate(Sum('merits'))['merits__sum'] or 0
        total_demerits = activities.aggregate(Sum('demerits'))['demerits__sum'] or 0
        
        context = {
            'student': student,
            'attendance': attendance,
            'grades': grades,
            'total_merits': total_merits,
            'total_demerits': total_demerits,
            'recent_activities': activities.order_by('-date')[:5]
        }
        
        return render(request, 'student/dashboard.html', context)
    except StudentRecord.DoesNotExist:
        messages.error(request, 'Student record not found')
        logout(request)
        return redirect('student_login')

def student_logout(request):
    logout(request)
    return redirect('student_login') 