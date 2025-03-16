from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from .models import UploadFiles, StudentRecord, ExcelUpload
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
        excel_file = request.FILES.get('excel_file')
        if excel_file and excel_file.name.endswith(('.xlsx', '.xls')):
            try:
                # Load the entire Excel file first to analyze it
                full_df = pd.read_excel(excel_file, sheet_name=None, header=None)
                
                # Determine which sheet to use (first sheet by default)
                sheet_name = list(full_df.keys())[0]
                if len(full_df.keys()) > 1:
                    # If multiple sheets, try to find one with student data
                    for sheet in full_df.keys():
                        sheet_df = full_df[sheet]
                        # Check if this sheet might contain student data
                        sheet_str = sheet_df.astype(str).values.flatten()
                        if any('student' in str(val).lower() for val in sheet_str):
                            sheet_name = sheet
                            break
                
                # Get the selected sheet
                df_raw = full_df[sheet_name]
                
                # Convert all data to string for easier handling
                df_str = df_raw.astype(str)
                
                # Look for student numbers in the entire sheet
                # Typical student numbers follow patterns like: 2020-12345 or 20-12345 or similar
                student_id_pattern = r'(?:\d{2,4}[-]?\d{4,6})|(?:\d{4,10})'
                
                # Find cells that might contain student IDs
                potential_id_locations = []
                for row_idx, row in enumerate(df_str.values):
                    for col_idx, cell in enumerate(row):
                        if pd.notna(cell) and re.search(student_id_pattern, str(cell)):
                            potential_id_locations.append((row_idx, col_idx))
                
                if not potential_id_locations:
                    messages.error(request, 'Could not identify any student ID patterns in the Excel file')
                    return redirect('upload_excel')
                
                # Determine the most common column for student IDs
                id_columns = [loc[1] for loc in potential_id_locations]
                student_id_col = max(set(id_columns), key=id_columns.count)
                
                # Identify rows that contain student records (having a student ID)
                student_rows = [loc[0] for loc in potential_id_locations if loc[1] == student_id_col]
                
                # Determine name column (usually right after or near student ID)
                name_col = student_id_col + 1
                # Try to find better name column by looking for common name patterns
                for col in range(max(0, student_id_col - 1), min(df_str.shape[1], student_id_col + 3)):
                    if col != student_id_col:
                        col_values = df_str.iloc[student_rows, col].tolist()
                        # Check if this column contains names (names typically have spaces and no digits)
                        if all(re.search(r'[A-Za-z]+\s+[A-Za-z]+', str(val)) for val in col_values if pd.notna(val) and val != 'nan'):
                            name_col = col
                            break
                
                # Try to identify gender column (usually contains only M/F or Male/Female)
                gender_col = None
                for col in range(df_str.shape[1]):
                    col_values = df_str.iloc[student_rows, col].tolist()
                    # Check if values are consistent with gender entries
                    gender_like_values = [
                        val for val in col_values 
                        if pd.notna(val) and val != 'nan' and 
                        (val.upper() in ['M', 'F', 'MALE', 'FEMALE'] or 
                         re.match(r'^[MF]$', val.upper()) or
                         'male' in val.lower() or 'female' in val.lower())
                    ]
                    if len(gender_like_values) >= len(student_rows) * 0.5:  # If at least half the rows have gender values
                        gender_col = col
                        break
                
                # Try to identify course column
                course_col = None
                course_keywords = ['course', 'program', 'degree', 'bsit', 'bscs', 'bs']
                for col in range(df_str.shape[1]):
                    col_values = [str(val).lower() for val in df_str.iloc[student_rows, col] if pd.notna(val) and val != 'nan']
                    # Check column header first
                    header_value = str(df_str.iloc[0, col]).lower() if df_str.shape[0] > 0 else ""
                    if any(keyword in header_value for keyword in course_keywords):
                        course_col = col
                        break
                    # Check if values in the column look like course codes
                    if all(re.search(r'^[A-Za-z]{2,6}$', val) or re.search(r'^BS[A-Za-z]{2,4}$', val) for val in col_values if val):
                        course_col = col
                        break
                
                # Try to identify year column
                year_col = None
                year_keywords = ['year', 'level', 'yr']
                for col in range(df_str.shape[1]):
                    col_values = [str(val).lower() for val in df_str.iloc[student_rows, col] if pd.notna(val) and val != 'nan']
                    # Check column header first
                    header_value = str(df_str.iloc[0, col]).lower() if df_str.shape[0] > 0 else ""
                    if any(keyword in header_value for keyword in year_keywords):
                        year_col = col
                        break
                    # Check if values in the column are years (1-5 typically)
                    if all(val in ['1', '2', '3', '4', '5', 'i', 'ii', 'iii', 'iv', 'v'] for val in col_values if val):
                        year_col = col
                        break
                
                # Clear existing records if requested
                if request.POST.get('clear_existing', False):
                    StudentRecord.objects.all().delete()
                
                records_created = 0
                records_skipped = 0
                
                # Process all identified student rows
                for row_idx in student_rows:
                    try:
                        # Get student number
                        student_no = str(df_raw.iloc[row_idx, student_id_col])
                        # Clean student number (remove any non-alphanumeric except dash)
                        student_no = re.sub(r'[^A-Za-z0-9\-]', '', student_no)
                        
                        # Skip if student_no is empty or just spaces
                        if not student_no or student_no.isspace() or student_no == 'nan':
                            records_skipped += 1
                            continue
                        
                        # Get name
                        name = str(df_raw.iloc[row_idx, name_col]) if name_col is not None else ''
                        name = name.strip() if name and name != 'nan' else ''
                        
                        # Get gender (default empty)
                        gender = ''
                        if gender_col is not None:
                            gender_value = str(df_raw.iloc[row_idx, gender_col]).strip()
                            if gender_value and gender_value != 'nan':
                                if gender_value.upper() in ['M', 'MALE']:
                                    gender = 'M'
                                elif gender_value.upper() in ['F', 'FEMALE']:
                                    gender = 'F'
                                else:
                                    gender = gender_value[0].upper()  # Just take first letter
                        
                        # Get course (default to 'BSINT')
                        course = 'BSINT'
                        if course_col is not None:
                            course_value = str(df_raw.iloc[row_idx, course_col]).strip()
                            if course_value and course_value != 'nan':
                                course = course_value
                        
                        # Get year - Simplified year handling
                        year = 4  # Default year level
                        if year_col is not None:
                            year_value = df_raw.iloc[row_idx, year_col]
                            if pd.notna(year_value):
                                try:
                                    # Try to convert to integer
                                    year = int(float(str(year_value).strip()))
                                    # Ensure year is between 1-5
                                    if year < 1 or year > 5:
                                        year = 4
                                except (ValueError, TypeError):
                                    # If conversion fails, try to handle roman numerals
                                    year_str = str(year_value).strip().upper()
                                    if year_str in ['I', '1', 'FIRST']:
                                        year = 1
                                    elif year_str in ['II', '2', 'SECOND']:
                                        year = 2
                                    elif year_str in ['III', '3', 'THIRD']:
                                        year = 3
                                    elif year_str in ['IV', '4', 'FOURTH']:
                                        year = 4
                                    elif year_str in ['V', '5', 'FIFTH']:
                                        year = 5
                                    else:
                                        year = 4  # Default if no valid year found
                        
                        # Log exact year extraction for debugging
                        print(f"Row {row_idx}: Student {student_no}, Year value in Excel: {df_raw.iloc[row_idx, year_col] if year_col is not None else 'N/A'}, Extracted year: {year}")
                        
                        # Check if record already exists
                        existing_record = StudentRecord.objects.filter(student_no=student_no).first()
                        
                        if existing_record:
                            # Update existing record
                            existing_record.name = name
                            existing_record.gender = gender
                            existing_record.course = course
                            existing_record.year = year
                            existing_record.save()
                            records_created += 1
                        else:
                            # Create new record
                            StudentRecord.objects.create(
                                student_no=student_no,
                                name=name,
                                gender=gender,
                                course=course,
                                year=year
                            )
                            records_created += 1
                        
                        print(f"Processed record {records_created}: {student_no} - {name} - Year: {year}")
                            
                    except Exception as row_error:
                        print(f"Error in row {row_idx+1}: {str(row_error)}")
                        records_skipped += 1
                        continue

                # Create upload record
                upload_record = ExcelUpload.objects.create(
                    file_name=excel_file.name,
                    total_records=records_created,
                    processed=True
                )
                
                messages.success(request, f'Successfully uploaded {records_created} student records! {records_skipped} records were skipped.')
                
                # Additional logging for debugging
                print(f"Total records found: {len(student_rows)}")
                print(f"Records created: {records_created}")
                print(f"Records skipped: {records_skipped}")
                
                return redirect('display_uploaded_tables')

            except Exception as e:
                print(f"File processing error: {str(e)}")
                messages.error(request, f'Error processing file: {str(e)}')
        else:
            messages.error(request, 'Please upload only Excel files (.xlsx, .xls)')
    
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