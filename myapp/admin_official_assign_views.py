from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from .models import Personnel, UploadFiles

@login_required
def assign_official(request):
    try:
        # Get the most recent uploaded table
        latest_upload = UploadFiles.objects.latest('created_at')
        table_name = latest_upload.table_name
        
        # Add assigned_personnel column if it doesn't exist
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                AND column_name = 'assigned_personnel'
            """)
            column_exists = cursor.fetchone()[0]
            
            if not column_exists:
                cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN assigned_personnel VARCHAR(255)")

            # Get all rows grouped by gender
            cursor.execute(f"""
                SELECT id, gender
                FROM `{table_name}`
                ORDER BY id
            """)
            all_rows = cursor.fetchall()

            # Get all available personnel
            male_personnel = list(Personnel.objects.filter(gender_assignment='male').values_list('first_name', 'last_name'))
            female_personnel = list(Personnel.objects.filter(gender_assignment='female').values_list('first_name', 'last_name'))

            # Process assignments
            male_count = len(male_personnel)
            female_count = len(female_personnel)
            assignments = []

            for row_id, gender in all_rows:
                if gender.lower() == 'male' and male_count > 0:
                    # Cycle through male personnel
                    male_index = (row_id - 1) % male_count
                    person = male_personnel[male_index]
                    assignments.append((f"{person[0]} {person[1]}", row_id))
                elif gender.lower() == 'female' and female_count > 0:
                    # Cycle through female personnel
                    female_index = (row_id - 1) % female_count
                    person = female_personnel[female_index]
                    assignments.append((f"{person[0]} {person[1]}", row_id))

            # Bulk update all assignments
            for assigned_name, row_id in assignments:
                cursor.execute(f"""
                    UPDATE `{table_name}`
                    SET assigned_personnel = %s
                    WHERE id = %s
                """, [assigned_name, row_id])

        messages.success(request, f'Successfully assigned {len(assignments)} rows! ({len(male_personnel)} male personnel and {len(female_personnel)} female personnel available)')
    except Exception as e:
        messages.error(request, f'Error during assignment: {str(e)}')
    
    return redirect('display_uploaded_tables') 