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

# Add this new model for the many-to-many relationship
class EventFlightGroup(models.Model):
    event = models.ForeignKey('Announcement', on_delete=models.CASCADE, related_name='event_flight_groups')
    flight_group = models.ForeignKey('FlightGroup', on_delete=models.CASCADE, related_name='event_groups')

    class Meta:
        unique_together = ('event', 'flight_group')

    def __str__(self):
        return f"{self.event.title} - {self.flight_group.name}"

# New model for personnel-student assignments
class PersonnelStudentAssignment(models.Model):
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='assigned_students')
    student = models.ForeignKey(StudentRecord, on_delete=models.CASCADE, related_name='assigned_personnel')
    assigned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student',)  # Each student can only be assigned to one personnel
        ordering = ['personnel__last_name', 'student__name']
    
    def __str__(self):
        return f"{self.student.name} assigned to {self.personnel.first_name} {self.personnel.last_name}"