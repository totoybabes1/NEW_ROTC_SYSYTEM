from django.urls import path, include

urlpatterns = [
    # ... other URL patterns ...
    path('personnel/', include('myapp.urls')),
] 