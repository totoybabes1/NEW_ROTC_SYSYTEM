from django.contrib import admin
from .models import Profile

# Custom admin panel for Profile model
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'profile_picture')
    
admin.site.register(Profile, ProfileAdmin)
