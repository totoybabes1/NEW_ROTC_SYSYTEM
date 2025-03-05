from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from .models import Personnel, UploadFiles, UploadedData, AttendanceRecord
from datetime import datetime
import json

@login_required
def personnel_attendance(request, personnel_id):
    """View for displaying individual personnel attendance history"""
    try:
        personnel = get_object_or_404(Personnel, id=personnel_id)
        
        # Get all attendance records for this personnel
        attendance_records = AttendanceRecord.objects.filter(
            personnel=personnel
        ).select_related('uploaded_data').order_by('-uploaded_data__date')
        
        # Calculate statistics
        total_records = attendance_records.count()
        present_count = attendance_records.filter(status='PRESENT').count()
        absent_count = attendance_records.filter(status='ABSENT').count()
        late_count = attendance_records.filter(status='LATE').count()
        
        attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
        
        context = {
            'personnel': personnel,
            'attendance_records': attendance_records,
            'stats': {
                'total': total_records,
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'attendance_rate': round(attendance_rate, 2)
            }
        }
        return render(request, 'attendance/personnel_attendance.html', context)
    
    except Personnel.DoesNotExist:
        messages.error(request, 'Personnel not found.')
        return redirect('manage_attendance')

@login_required
def view_attendance(request, upload_id=None):
    try:
        upload = UploadFiles.objects.get(id=upload_id) if upload_id else UploadFiles.objects.latest('created_at')
        
        # Get attendance data for the current user's personnel
        personnel = Personnel.objects.get(user=request.user)
        attendance_data = UploadedData.objects.filter(
            assigned_personnel=personnel,
            upload_file=upload
        ).select_related('upload_file')

        attendance_records = []
        for data in attendance_data:
            record = AttendanceRecord.objects.filter(
                uploaded_data=data,
                personnel=personnel
            ).first()

            attendance_records.append({
                'data': data,
                'record': record,
                'raw_data': data.extra_data
            })

        context = {
            'upload': upload,
            'attendance_records': attendance_records,
            'today': datetime.now(),
        }
        return render(request, 'attendance/view_attendance.html', context)
    
    except UploadFiles.DoesNotExist:
        messages.error(request, 'No uploads found.')
        return redirect('manage_attendance')

@login_required
def mark_attendance(request):
    if request.method == 'POST':
        data_id = request.POST.get('data_id')
        status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')

        try:
            uploaded_data = UploadedData.objects.get(id=data_id)
            personnel = Personnel.objects.get(user=request.user)

            with transaction.atomic():
                record, created = AttendanceRecord.objects.update_or_create(
                    uploaded_data=uploaded_data,
                    personnel=personnel,
                    defaults={
                        'status': status,
                        'remarks': remarks,
                        'marked_by': request.user
                    }
                )
            
            messages.success(request, 'Attendance marked successfully!')
            
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
        
        return redirect('view_attendance', upload_id=uploaded_data.upload_file.id)
    
    return redirect('manage_attendance')

@login_required
def manage_attendance(request):
    """View for managing attendance records"""
    uploads = UploadFiles.objects.all().order_by('-created_at')
    context = {
        'uploads': uploads,
    }
    return render(request, 'attendance/manage_attendance.html', context) 