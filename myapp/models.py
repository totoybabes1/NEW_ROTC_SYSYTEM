from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Profile model for storing additional user information and this is part of the admin
class Profile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)  # Links to Django's built-in User model
    bio = models.TextField(blank=True)  # Optional biography text
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)  # Optional profile picture
    last_activity = models.DateTimeField(auto_now=True)  # Add this field
    activity_log = models.JSONField(default=list, blank=True)  # Add this field

    def log_activity(self, action):
        """Log an activity with timestamp"""
        activity = {
            'action': action,
            'timestamp': timezone.now().isoformat()
        }
        if not self.activity_log:
            self.activity_log = []
        self.activity_log.append(activity)
        self.save()

    def __str__(self):
        return self.user.username

# FlightGroup model for organizing personnel into groups/squadrons
class FlightGroup(models.Model):
    name = models.CharField(max_length=100)  # Name of the flight group
    description = models.TextField()  # Description of the flight group
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'myapp'

    def __str__(self):
        return self.name

# Personnel model for storing detailed information about each member
class Personnel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Links to Django's User model
    first_name = models.CharField(max_length=100)  # Member's first name
    last_name = models.CharField(max_length=100)  # Member's last name
    position = models.CharField(max_length=100)  # Role/position in the organization
    status = models.CharField(max_length=100)  # Current status (e.g., active, inactive)
    student_id = models.CharField(max_length=100)  # Unique student identifier
    age = models.CharField(max_length=100)  # Member's age
    gender = models.CharField(max_length=100)  # Member's gender
    phone_number = models.CharField(max_length=100)  # Contact number
    date_joined = models.DateField(auto_now_add=True)  # Date when member joined
    profile_picture = models.ImageField(upload_to='member_pics/', blank=True)  # Optional profile picture
    flight_group = models.ForeignKey(FlightGroup, on_delete=models.SET_NULL, null=True, blank=True)  # Associated flight group
    gender_assignment = models.CharField(max_length=100, blank=True, null=True)  # Gender assignment for accommodation

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position}"

# Model for tracking uploaded files
class UploadFiles(models.Model):
    table_name = models.CharField(max_length=255)  # Name of the table/category for uploaded files
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of upload

    def __str__(self):
        return self.table_name

# Model for tracking user login/logout activity
class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User who performed the activity
    activity_type = models.CharField(max_length=10)  # Type of activity (login/logout)
    timestamp = models.DateTimeField(auto_now_add=True)  # When the activity occurred

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"

# Model for managing announcements and events
class Announcement(models.Model):
    title = models.CharField(max_length=200)  # Title of the announcement
    content = models.TextField()  # Content of the announcement
    date = models.DateTimeField(auto_now_add=True)  # When the announcement was created
    flight_group = models.ForeignKey(FlightGroup, on_delete=models.CASCADE, related_name='announcements')  # Associated flight group
    is_event = models.BooleanField(default=False)  # Whether this is an event announcement
    event_date = models.DateTimeField(null=True, blank=True)  # Date of the event if applicable
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # User who created the announcement

    class Meta:
        ordering = ['-date']  # Orders announcements by date, newest first

    def __str__(self):
        return f"{self.title} - {self.flight_group.name}"

class UploadedData(models.Model):
    """Model to store the copied data from Excel uploads"""
    upload_file = models.ForeignKey(UploadFiles, on_delete=models.CASCADE)
    assigned_personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='assigned_data')
    # Common fields that might be in your Excel
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    activity = models.CharField(max_length=255, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    # Store any additional Excel columns as JSON
    extra_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.assigned_personnel} - {self.date} - {self.activity}"

class AttendanceRecord(models.Model):
    """Model to store attendance for each uploaded data entry"""
    uploaded_data = models.OneToOneField(UploadedData, on_delete=models.CASCADE, related_name='attendance')
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE)
    status_choices = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused')
    ]
    status = models.CharField(max_length=20, choices=status_choices)
    remarks = models.TextField(blank=True, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.personnel} - {self.uploaded_data.date} - {self.status}"

# Add this new model
class StudentRecord(models.Model):
    student_no = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    course = models.CharField(max_length=20)
    year = models.IntegerField()
    status = models.CharField(max_length=10, choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')], default='ACTIVE')
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_no} - {self.name}"

    class Meta:
        ordering = ['student_no']

class ExcelUpload(models.Model):
    file_name = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    total_records = models.IntegerField(default=0)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.file_name} ({self.upload_date})"

    class Meta:
        ordering = ['-upload_date']