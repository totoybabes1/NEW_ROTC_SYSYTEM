from django import template
from myapp.models import StudentAttendance
from django.utils import timezone

register = template.Library()

@register.filter
def get_attendance_status(student_id, personnel_id):
    """Get today's attendance status for a student"""
    today = timezone.now().date()
    try:
        attendance = StudentAttendance.objects.get(
            student_id=student_id,
            personnel_id=personnel_id,
            date=today
        )
        return attendance.status
    except StudentAttendance.DoesNotExist:
        return "Not recorded"

@register.filter
def get_attendance_status_class(student_id, personnel_id):
    """Get CSS class for today's attendance status for a student"""
    status = get_attendance_status(student_id, personnel_id)
    status_classes = {
        'PRESENT': 'bg-success',
        'LATE': 'bg-warning',
        'ABSENT': 'bg-danger',
        'EXCUSED': 'bg-info',
        'Not recorded': 'bg-secondary'
    }
    return status_classes.get(status, 'bg-secondary')

@register.filter
def get_attendance_badge_class(status):
    """Return the appropriate Bootstrap badge class for an attendance status"""
    status_classes = {
        'PRESENT': 'bg-success',
        'LATE': 'bg-warning',
        'ABSENT': 'bg-danger',
        'EXCUSED': 'bg-info',
        'Not recorded': 'bg-secondary'
    }
    return status_classes.get(status, 'bg-secondary') 

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    return dictionary.get(key, '')