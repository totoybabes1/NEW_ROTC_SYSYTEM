from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import connection
from .models import UploadFiles

@login_required
def display_uploaded_tables(request):
    # Fetch all uploaded files to get their table names
    uploaded_files = UploadFiles.objects.all()
    tables_data = []

    for file in uploaded_files:
        table_name = file.table_name
        with connection.cursor() as cursor:
            # Check if assigned_personnel column exists
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                AND column_name = 'assigned_personnel'
            """)
            has_assignments = cursor.fetchone()[0] > 0
            
            # Select all columns including assigned_personnel if it exists
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            
            tables_data.append({
                'table_name': table_name,
                'columns': columns,
                'rows': rows,
                'has_assignments': has_assignments
            })

    return render(request, 'admin/admin_display_uploaded_tables.html', {'tables_data': tables_data})    