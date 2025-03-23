from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from .models import StudentRecord, ExcelUpload
import pandas as pd
import numpy as np
import uuid
from datetime import datetime
from django.urls import reverse
from django.http import HttpResponse
import os
import re

@login_required
def upload_excel(request):
    if request.method == 'POST':
        excel_files = request.FILES.getlist('excel_files')
        if excel_files:
            total_records_created = 0
            successful_files = 0
            failed_files = 0
            
            for excel_file in excel_files:
                if excel_file.name.endswith(('.xlsx', '.xls')):
                    try:
                        # Read Excel file with explicit header=None to avoid skipping first row
                        df = pd.read_excel(excel_file, header=None)
                        
                        # Find the header row and data rows
                        header_row = None
                        data_start_row = 0
                        
                        # Look for rows that might contain headers like "Student No." or "Name"
                        for i, row in df.iterrows():
                            row_str = ' '.join(str(x).lower() for x in row if pd.notna(x))
                            if ('student' in row_str and ('no' in row_str or 'number' in row_str)) or 'name' in row_str:
                                header_row = i
                                data_start_row = i + 1
                                break
                        
                        # If we couldn't find a header row, try to detect the first row with student numbers
                        if header_row is None:
                            # Look for a pattern like student numbers (e.g., 20230056)
                            for i, row in df.iterrows():
                                for cell in row:
                                    if pd.notna(cell) and isinstance(cell, (int, str)) and re.match(r'\d{8}', str(cell)):
                                        data_start_row = i
                                        break
                                if data_start_row > 0:
                                    break
                        
                        # Find columns for student data
                        student_no_col = None
                        name_col = None
                        gender_col = None
                        course_col = None
                        year_col = None
                        
                        # If we found a header row, use it to identify columns
                        if header_row is not None:
                            for j, cell in enumerate(df.iloc[header_row]):
                                if pd.notna(cell):
                                    cell_str = str(cell).lower()
                                    if 'student' in cell_str and ('no' in cell_str or 'number' in cell_str):
                                        student_no_col = j
                                    elif 'name' in cell_str:
                                        name_col = j
                                    elif 'gender' in cell_str or 'sex' in cell_str:
                                        gender_col = j
                                    elif 'course' in cell_str or 'program' in cell_str:
                                        course_col = j
                                    elif 'year' in cell_str:
                                        year_col = j
                        
                        # If we couldn't identify columns from headers, make educated guesses
                        if student_no_col is None:
                            # Assume first column with numeric values that look like IDs
                            for j in range(df.shape[1]):
                                col_values = df.iloc[data_start_row:, j]
                                if col_values.apply(lambda x: pd.notna(x) and re.match(r'\d{8}', str(x))).any():
                                    student_no_col = j
                                    break
                        
                        if name_col is None and student_no_col is not None:
                            # Assume name is in the column after student number
                            name_col = student_no_col + 1
                        
                        if gender_col is None:
                            # Look for a column with M/F values
                            for j in range(df.shape[1]):
                                col_values = df.iloc[data_start_row:, j].astype(str)
                                if col_values.apply(lambda x: x.upper() in ['M', 'F', 'MALE', 'FEMALE']).mean() > 0.3:
                                    gender_col = j
                                    break
                        
                        if course_col is None:
                            # Look for a column with course-like values (e.g., BSCRM, BSIT)
                            for j in range(df.shape[1]):
                                col_values = df.iloc[data_start_row:, j].astype(str)
                                if col_values.apply(lambda x: bool(re.match(r'BS[A-Z]{2,4}', x.upper()) if isinstance(x, str) else False)).mean() > 0.2:
                                    course_col = j
                                    break
                        
                        if year_col is None:
                            # Look for a column with year values (1-5)
                            for j in range(df.shape[1]):
                                col_values = df.iloc[data_start_row:, j]
                                if col_values.apply(lambda x: pd.notna(x) and str(x) in ['1', '2', '3', '4', '5']).mean() > 0.3:
                                    year_col = j
                                    break
                        
                        # Debug information
                        print(f"Header row: {header_row}, Data start row: {data_start_row}")
                        print(f"Student No. column: {student_no_col}, Name column: {name_col}")
                        print(f"Gender column: {gender_col}, Course column: {course_col}, Year column: {year_col}")
                        
                        # Process data rows
                        records_created = 0
                        records_skipped = 0
                        skipped_rows = []
                        
                        for i in range(data_start_row, len(df)):
                            row = df.iloc[i]
                            
                            # Skip empty rows
                            if row.isna().all():
                                continue
                            
                            try:
                                # Extract student number - handle different formats
                                student_no = None
                                if student_no_col is not None:
                                    if pd.notna(row[student_no_col]):
                                        # Convert to string and clean up
                                        student_no = str(row[student_no_col]).strip()
                                        # If it's a float, convert to int first to remove decimal
                                        if isinstance(row[student_no_col], float):
                                            student_no = str(int(row[student_no_col]))
                                
                                # If still no student number, try to find it in any column
                                if not student_no:
                                    for j, cell in enumerate(row):
                                        if pd.notna(cell) and isinstance(cell, (int, float, str)):
                                            cell_str = str(cell)
                                            if re.match(r'\d{8}', cell_str):
                                                student_no = cell_str
                                                break
                                
                                if not student_no:
                                    # Skip rows without student numbers
                                    skipped_rows.append(f"Row {i+1}: No student number found")
                                    records_skipped += 1
                                    continue
                                
                                # Extract name
                                name = ""
                                if name_col is not None and pd.notna(row[name_col]):
                                    name = str(row[name_col]).strip()
                                
                                # If no name found, try to find it in any column
                                if not name:
                                    for j, cell in enumerate(row):
                                        if pd.notna(cell) and isinstance(cell, str) and ',' in cell and len(cell) > 5:
                                            name = cell.strip()
                                            break
                                
                                if not name:
                                    name = f"Student {student_no}"  # Default name if none found
                                
                                # Extract gender
                                gender = "M"  # Default gender
                                if gender_col is not None and pd.notna(row[gender_col]):
                                    gender_val = str(row[gender_col]).strip().upper()
                                    if gender_val in ['M', 'MALE']:
                                        gender = 'M'
                                    elif gender_val in ['F', 'FEMALE']:
                                        gender = 'F'
                                    else:
                                        # Take first character if it's M or F
                                        first_char = gender_val[0] if gender_val else ''
                                        gender = first_char if first_char in ['M', 'F'] else 'M'
                                
                                # Extract course
                                course = "BSCRM"  # Default course
                                if course_col is not None and pd.notna(row[course_col]):
                                    course_val = str(row[course_col]).strip().upper()
                                    # Ensure course is stored as text, not a number
                                    if course_val.isdigit():
                                        course = f"BS{course_val}"
                                    else:
                                        course = course_val
                                
                                # Extract year
                                year = 2  # Default to year 2
                                if year_col is not None and pd.notna(row[year_col]):
                                    year_val = row[year_col]
                                    if isinstance(year_val, (int, float)) and 1 <= year_val <= 5:
                                        year = int(year_val)
                                    elif isinstance(year_val, str):
                                        year_str = year_val.strip()
                                        if year_str.isdigit() and 1 <= int(year_str) <= 5:
                                            year = int(year_str)
                                        elif year_str.upper() in ['I', 'FIRST', '1ST']:
                                            year = 1
                                        elif year_str.upper() in ['II', 'SECOND', '2ND']:
                                            year = 2
                                        elif year_str.upper() in ['III', 'THIRD', '3RD']:
                                            year = 3
                                        elif year_str.upper() in ['IV', 'FOURTH', '4TH']:
                                            year = 4
                                        elif year_str.upper() in ['V', 'FIFTH', '5TH']:
                                            year = 5
                                
                                # Check if student already exists
                                existing_student = StudentRecord.objects.filter(student_no=student_no).first()
                                
                                if existing_student:
                                    # Update existing record
                                    if name:
                                        existing_student.name = name
                                    if gender:
                                        existing_student.gender = gender
                                    if course:
                                        existing_student.course = course
                                    existing_student.year = year
                                    existing_student.save()
                                else:
                                    # Create new record
                                    StudentRecord.objects.create(
                                        student_no=student_no,
                                        name=name,
                                        gender=gender,
                                        course=course,
                                        year=year,
                                        status='ACTIVE'
                                    )
                                
                                records_created += 1
                                
                            except Exception as e:
                                error_msg = f"Row {i+1}: {str(e)}"
                                print(error_msg)
                                skipped_rows.append(error_msg)
                                records_skipped += 1
                        
                        # Create upload record
                        ExcelUpload.objects.create(
                            file_name=excel_file.name,
                            total_records=records_created,
                            processed=True
                        )
                        
                        total_records_created += records_created
                        successful_files += 1
                        
                    except Exception as e:
                        failed_files += 1
                        messages.error(request, f'Error processing file {excel_file.name}: {str(e)}')
                else:
                    failed_files += 1
                    messages.error(request, f'File {excel_file.name} is not an Excel file (.xlsx, .xls)')
            
            if successful_files > 0:
                success_msg = f'Successfully uploaded {total_records_created} student records from {successful_files} file(s)!'
                if failed_files > 0:
                    success_msg += f' {failed_files} file(s) failed to process.'
                messages.success(request, success_msg)
                return redirect('display_uploaded_tables')
            else:
                messages.error(request, 'No files were successfully processed.')
        else:
            messages.error(request, 'Please select at least one Excel file to upload.')
    
    uploads = ExcelUpload.objects.all().order_by('-upload_date')
    return render(request, 'upload/excel_upload.html', {'uploads': uploads})

@login_required
def display_uploaded_tables(request):
    students = StudentRecord.objects.all().order_by('student_no')
    uploads = ExcelUpload.objects.all().order_by('-upload_date')
    
    # Allow searching/filtering of records
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            student_no__icontains=search_query
        ) | students.filter(
            name__icontains=search_query
        )
    
    context = {
        'students': students,
        'uploads': uploads,
        'search_query': search_query,
        'total_students': students.count(),
        'total_uploads': uploads.count()
    }
    return render(request, 'upload/display_tables.html', context)

@login_required
def view_excel_content(request, file_id):
    try:
        # This function references the missing UploadFiles model
        # Let's modify it to use ExcelUpload instead
        excel_upload = ExcelUpload.objects.get(id=file_id)
        
        # Since ExcelUpload might not have the same structure as UploadFiles,
        # we'll need to adjust the logic here
        context = {
            'file': excel_upload,
            'selected_file_id': file_id,
            'uploaded_files': ExcelUpload.objects.all(),
            'total_files': ExcelUpload.objects.count()
        }
        return render(request, 'upload/excel_upload.html', context)
    except Exception as e:
        messages.error(request, f'Error viewing file: {str(e)}')
    return redirect('upload_excel')

@login_required
def delete_excel(request, file_id):
    try:
        excel_upload = ExcelUpload.objects.get(id=file_id)
        excel_upload.delete()
        messages.success(request, 'Upload record deleted successfully!')
    except ExcelUpload.DoesNotExist:
        messages.error(request, 'Upload record not found!')
    except Exception as e:
        messages.error(request, f'Error deleting upload record: {str(e)}')
    
    return redirect('display_uploaded_tables')

@login_required
def delete_uploaded_file(request, file_id):
    try:
        # Replace UploadFiles with ExcelUpload
        file_metadata = ExcelUpload.objects.get(id=file_id)
        
        # ExcelUpload might not have a table_name field, so we'll adjust this
        # If you need to drop a table, you would need to know its name
        
        # Delete the metadata entry
        file_metadata.delete()
        
        messages.success(request, 'File deleted successfully!')
    except ExcelUpload.DoesNotExist:
        messages.error(request, 'File not found!')
    except Exception as e:
        messages.error(request, f'Error deleting file: {str(e)}')
    
    return redirect('upload_excel')

@login_required
def download_uploaded_file(request, file_id):
    try:
        # Replace UploadFiles with ExcelUpload
        file_metadata = ExcelUpload.objects.get(id=file_id)
        
        # Since ExcelUpload might not have table_name, adjust accordingly
        file_name = file_metadata.file_name
        
        # Define the file path (assuming files are stored in a specific directory)
        file_path = os.path.join('download', file_name)
        
        # Check if the file exists
        if not os.path.exists(file_path):
            messages.error(request, 'File not found!')
            return redirect('upload_excel')
        
        # Serve the file as a download
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    except ExcelUpload.DoesNotExist:
        messages.error(request, 'File not found!')
    except Exception as e:
        messages.error(request, f'Error downloading file: {str(e)}')
    
    return redirect('upload_excel')

@login_required
def edit_student_record(request, student_id):
    if request.method == 'POST':
        try:
            student = StudentRecord.objects.get(id=student_id)
            student.student_no = request.POST.get('student_no')
            student.name = request.POST.get('name')
            student.gender = request.POST.get('gender')
            student.course = request.POST.get('course')
            student.year = request.POST.get('year')
            student.save()
            messages.success(request, 'Student record updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating record: {str(e)}')
    return redirect('display_uploaded_tables')

@login_required
def delete_student_record(request, student_id):
    try:
        student = StudentRecord.objects.get(id=student_id)
        student.delete()
        messages.success(request, 'Student record deleted successfully!')
    except StudentRecord.DoesNotExist:
        messages.error(request, 'Student record not found!')
    except Exception as e:
        messages.error(request, f'Error deleting record: {str(e)}')
    
    return redirect('display_uploaded_tables')

@login_required
def export_students(request):
    try:
        students = StudentRecord.objects.all().order_by('student_no')
        
        # Create a DataFrame from student records
        data = {
            'Student No': [s.student_no for s in students],
            'Name': [s.name for s in students],
            'Gender': [s.gender for s in students],
            'Course': [s.course for s in students],
            'Year': [s.year for s in students]
        }
        df = pd.DataFrame(data)
        
        # Create a response with the Excel file
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="student_records.xlsx"'
        
        # Write the DataFrame to the response
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')
        
        return response
    except Exception as e:
        messages.error(request, f'Error exporting records: {str(e)}')
    
    return redirect('display_uploaded_tables')