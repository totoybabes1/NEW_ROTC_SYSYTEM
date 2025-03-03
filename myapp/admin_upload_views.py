from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from .models import UploadFiles
import pandas as pd
import uuid
from datetime import datetime
from django.urls import reverse
from django.http import HttpResponse
import os

@login_required
def upload_excel(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if excel_file and excel_file.name.endswith(('.xlsx', '.xls')):
            try:
                # Save the file to the filesystem
                file_directory = 'download'  # Update this to your actual file directory
                if not os.path.exists(file_directory):
                    os.makedirs(file_directory)
                
                file_path = os.path.join(file_directory, excel_file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in excel_file.chunks():
                        destination.write(chunk)
                
                # Process the file as before
                df = pd.read_excel(file_path)
                
                # Generate a table name based on the current date
                current_date = datetime.now().strftime("%d_%m_%Y")
                table_name = f"upload_{current_date}"
                
                # Create table with columns matching Excel headers
                columns = df.columns
                column_definitions = ", ".join([f"`{col}` TEXT" for col in columns])
                create_table_sql = f"CREATE TABLE `{table_name}` (id INT AUTO_INCREMENT PRIMARY KEY, {column_definitions})"
                
                with connection.cursor() as cursor:
                    cursor.execute(create_table_sql)
                
                # Insert data into the new table
                for _, row in df.iterrows():
                    values = "', '".join(str(value).replace("'", "''") for value in row)  # Escape single quotes in values
                    insert_sql = f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in columns])}) VALUES ('{values}')"
                    with connection.cursor() as cursor:
                        cursor.execute(insert_sql)
                
                # Save metadata
                UploadFiles.objects.create(table_name=table_name)
                
                messages.success(request, f'Excel file uploaded and data stored in table {table_name}!')
                return redirect('upload_excel')
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
        else:
            messages.error(request, 'Please upload only Excel files (.xlsx, .xls)')
    
    # Fetch all uploaded files
    uploaded_files = UploadFiles.objects.all()
    total_files = uploaded_files.count()
    
    return render(request, 'upload/excel_upload.html', {'total_files': total_files, 'uploaded_files': uploaded_files})

@login_required
def view_excel_content(request, file_id):
    try:
        # Retrieve the table name from metadata
        table_metadata = UploadFiles.objects.get(id=file_id)
        table_name = table_metadata.table_name
        
        # Fetch data from the dynamically created table
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
        
        context = {
            'columns': columns,
            'rows': rows,
            'selected_file_id': file_id,
            'total_rows': len(rows),
            'uploaded_files': UploadFiles.objects.all(),
            'total_files': UploadFiles.objects.count()
        }
        return render(request, 'upload/excel_upload.html', context)
    except Exception as e:
        messages.error(request, f'Error viewing file: {str(e)}')
    return redirect('upload_excel')

@login_required
def delete_excel(request, file_id):
    try:
        # Retrieve the table name from metadata
        file_metadata = UploadFiles.objects.get(id=file_id)
        table_name = file_metadata.table_name
        
        # Drop the table from the database
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        
        # Delete the metadata entry
        file_metadata.delete()
        
        messages.success(request, 'File deleted successfully!')
    except UploadFiles.DoesNotExist:
        messages.error(request, 'File not found!')
    except Exception as e:
        messages.error(request, f'Error deleting file: {str(e)}')
    
    return redirect('upload_excel')

@login_required
def delete_uploaded_file(request, file_id):
    try:
        # Retrieve the table name from metadata
        file_metadata = UploadFiles.objects.get(id=file_id)
        table_name = file_metadata.table_name
        
        # Drop the table from the database
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        
        # Delete the metadata entry
        file_metadata.delete()
        
        messages.success(request, 'File deleted successfully!')
    except UploadFiles.DoesNotExist:
        messages.error(request, 'File not found!')
    except Exception as e:
        messages.error(request, f'Error deleting file: {str(e)}')
    
    return redirect('upload_excel')

@login_required
def download_uploaded_file(request, file_id):
    try:
        # Retrieve the table name from metadata
        file_metadata = UploadFiles.objects.get(id=file_id)
        table_name = file_metadata.table_name
        
        # Define the file path (assuming files are stored in a specific directory)
        file_path = os.path.join('download', f"{table_name}.xlsx")
        
        # Check if the file exists
        if not os.path.exists(file_path):
            messages.error(request, 'File not found!')
            return redirect('upload_excel')
        
        # Serve the file as a download
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{table_name}.xlsx"'
            return response
    except UploadFiles.DoesNotExist:
        messages.error(request, 'File not found!')
    except Exception as e:
        messages.error(request, f'Error downloading file: {str(e)}')
    
    return redirect('upload_excel') 