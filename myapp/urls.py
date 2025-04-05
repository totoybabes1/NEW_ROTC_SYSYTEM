from django.urls import path
from . import admin_views, admin_member_views, admin_group_views, admin_upload_views, admin_assign_views, admin_uploadfiles_display_views, admin_profile_views, personnel_views, admin_event_calendar_views, admin_assigned_personnel_views, personnel_student_views, personnel_activity_grading_views, student_attendance_views, student_views, homepage_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Homepage URLs
    path('', homepage_views.home, name='home'),
    path('login/', homepage_views.login_view, name='login'),
    path('logout/', homepage_views.logout_view, name='logout'),
    path('admin-login/', homepage_views.admin_login, name='admin_login'),

    # Admin Page URLs
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),

    # Admin Group URLs
    path('admin-flight-groups/', admin_member_views.add_flight_group, name='admin_flight_groups'),
    path('edit-flight-group/<int:group_id>/', admin_member_views.edit_flight_group, name='edit_flight_group'),
    path('delete-flight-group/<int:group_id>/', admin_member_views.delete_flight_group, name='delete_flight_group'),

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
    path('edit-student/<int:student_id>/', admin_upload_views.edit_student_record, name='edit_student_record'),
    path('delete-excel/<int:upload_id>/', admin_uploadfiles_display_views.delete_excel_upload, name='delete_excel_upload'),
    path('edit-student/', admin_uploadfiles_display_views.edit_student_record, name='edit_student_record'),
    path('delete-student/', admin_uploadfiles_display_views.delete_student_record, name='delete_student_record'),
    path('manage-semester/', admin_upload_views.manage_semester, name='manage_semester'),
    path('set-active-semester/', admin_upload_views.set_active_semester, name='set_active_semester'),
    path('assign-semester-to-students/', admin_upload_views.assign_semester_to_students, name='assign_semester_to_students'),
    path('toggle-semester-status/', admin_upload_views.toggle_semester_status, name='toggle_semester_status'),

    path('api/activities/', admin_views.get_activities, name='get_activities'),

    # Personnel URLs
    path('personnel/logout/', homepage_views.logout_view, name='personnel_logout'),
    path('personnel/dashboard/', personnel_views.personnel_dashboard, name='personnel_dashboard'),
    path('personnel/profile/', personnel_views.personnel_profile, name='personnel_profile'),

    path('api/quick-stats/', admin_views.get_quick_stats, name='get_quick_stats'),
    path('api/detailed-stats/', admin_views.get_detailed_stats, name='get_detailed_stats'),

    # Event Calendar URLs
    path('admin-event-calendar/', admin_event_calendar_views.admin_event_calendar, name='admin_event_calendar'),
    path('add-event/', admin_event_calendar_views.add_event, name='add_event'),
    path('edit-event/<int:event_id>/', admin_event_calendar_views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', admin_event_calendar_views.delete_event, name='delete_event'),
    path('get-event-details/<int:event_id>/', admin_event_calendar_views.get_event_details, name='get_event_details'),
    path('export-events-pdf/', admin_event_calendar_views.export_events_pdf, name='export_events_pdf'),

    # Assigned Personnel URLs
    path('admin-assigned-personnel/', admin_assigned_personnel_views.assigned_personnel_list, name='assigned_personnel_list'),
    path('auto-assign-students/', admin_assigned_personnel_views.auto_assign_students, name='auto_assign_students'),
    path('manual-assign-student/', admin_assigned_personnel_views.manual_assign_student, name='manual_assign_student'),
    path('remove-student-assignment/<int:assignment_id>/', admin_assigned_personnel_views.remove_student_assignment, name='remove_student_assignment'),
    path('reassign-student/', admin_assigned_personnel_views.reassign_student, name='reassign_student'),
    path('reset-all-assignments/', admin_assigned_personnel_views.reset_all_assignments, name='reset_all_assignments'),
    path('handle-special-cases/', admin_assigned_personnel_views.handle_special_cases, name='handle_special_cases'),
    path('remove-special-case/<int:case_id>/', admin_assigned_personnel_views.remove_special_case, name='remove_special_case'),
    path('bulk-remove-special-cases/', admin_assigned_personnel_views.bulk_remove_special_cases, name='bulk_remove_special_cases'),
    path('manual-special-case-assignment/', 
         admin_assigned_personnel_views.manual_special_case_assignment, 
         name='manual_special_case_assignment'),

    # Personnel Student URLs
    path('personnel/assigned-students/', personnel_student_views.view_assigned_students, name='view_students_assigned'),
    path('personnel/student-details/<int:student_id>/', personnel_student_views.get_student_details, name='get_student_details'),
    path('personnel/filter-students/', personnel_student_views.filter_students, name='filter_students'),

    # Activity and Grading URLs
    path('personnel/activity-record/', personnel_activity_grading_views.activity_record, name='activity_record'),
    path('personnel/compute-grades/', personnel_activity_grading_views.compute_grades, name='compute_grades'),
    path('personnel/view-grades/', personnel_activity_grading_views.view_grades, name='view_grades'),
    path('personnel/export-grades/<str:format>/', personnel_activity_grading_views.export_grades, name='export_grades'),
    path('api/student-activities/<int:student_id>/', 
         personnel_activity_grading_views.get_student_activities, 
         name='get_student_activities'),
    path('api/semester-students/<int:semester_id>/', 
         personnel_activity_grading_views.get_semester_students, 
         name='get_semester_students'),

    # Attendance URLs
    path('personnel/record-attendance/', student_attendance_views.record_attendance, name='record_attendance'),
    path('personnel/view-attendance/', student_attendance_views.view_attendance, name='view_attendance'),
    path('api/student-attendance/<int:student_id>/', 
         student_attendance_views.get_student_attendance, 
         name='get_student_attendance'),

    # Student URLs
    path('student/login/', homepage_views.login_view, name='login'),
    path('student/dashboard/', student_views.student_dashboard, name='student_dashboard'),
    path('student/profile/', student_views.student_profile, name='student_profile'),
    path('student/attendance/', student_views.student_attendance, name='student_attendance'),
    path('student/activities/', student_views.student_activities, name='student_activities'),
    path('student/logout/', homepage_views.logout_view, name='student_logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
