from django.urls import path
from . import admin_views, admin_member_views, admin_group_views, admin_upload_views, admin_assign_views, admin_uploadfiles_display_views, admin_profile_views, admin_official_assign_views, personnel_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Page URLs
    path('', admin_views.home, name='home'),
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('login/', admin_views.admin_login, name='login'),
    path('logout/', admin_views.admin_logout, name='logout'),

    # Admin Group URLs
    path('admin-flight-groups/', admin_group_views.flight_groups, name='admin_flight_groups'),
    path('admin-flight-groups/edit/<int:group_id>/', admin_group_views.edit_flight_group, name='edit_flight_group'),
    path('admin-flight-groups/delete/<int:group_id>/', admin_group_views.delete_flight_group, name='delete_flight_group'),

    # Personnel Admin URLs
    path('admin-personnel/', admin_member_views.personnel_list, name='admin_personnel_list'),
    path('admin-personnel/add/', admin_member_views.add_personnel, name='add_personnel'),
    path('admin-personnel/edit/<int:personnel_id>/', admin_member_views.edit_personnel, name='edit_personnel'),
    path('admin-personnel/delete/<int:personnel_id>/', admin_member_views.delete_personnel, name='delete_personnel'),
    path('admin-personnel/bulk-delete/', admin_member_views.bulk_delete_personnel, name='bulk_delete_personnel'),
    path('admin-personnel/assign-gender/', admin_assign_views.assign_gender, name='assign_gender'),
    
    # Admin Profile
    path('profile/', admin_profile_views.admin_profile, name='admin_profile'),


    # Upload URLs
    path('admin-upload/', admin_upload_views.upload_excel, name='upload_excel'),
    path('admin-upload/delete/<int:file_id>/', admin_upload_views.delete_excel, name='delete_excel'),
    path('admin-upload/view/<str:file_id>/', admin_upload_views.view_excel_content, name='view_excel_content'),
    path('delete_uploaded_file/<int:file_id>/', admin_upload_views.delete_uploaded_file, name='delete_uploaded_file'),
    path('admin-upload/download/<int:file_id>/', admin_upload_views.download_uploaded_file, name='download_uploaded_file'),
    path('admin-uploaded-tables/', admin_uploadfiles_display_views.display_uploaded_tables, name='display_uploaded_tables'),

    path('api/activities/', admin_views.get_activities, name='get_activities'),

    path('admin-assign-official/', admin_official_assign_views.assign_official, name='assign_official'),

    # Personnel URLs
    path('personnel/login/', personnel_views.personnel_login, name='personnel_login'),
    path('personnel/logout/', personnel_views.personnel_logout, name='personnel_logout'),
    path('personnel/dashboard/', personnel_views.personnel_dashboard, name='personnel_dashboard'),
    path('personnel/profile/', personnel_views.personnel_profile, name='personnel_profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
