from django.db import models
from django.contrib.auth.models import User

# Profile model for storing additional user information and this is part of the admin
class Profile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)  # Links to Django's built-in User model
    bio = models.TextField(blank=True)  # Optional biography text
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)  # Optional profile picture

    def __str__(self):
        return self.user.username

# FlightGroup model for organizing personnel into groups/squadrons
class FlightGroup(models.Model):
    name = models.CharField(max_length=100)  # Name of the flight group
    description = models.TextField()  # Description of the flight group

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