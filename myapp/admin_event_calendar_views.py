from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Announcement, FlightGroup, EventFlightGroup
from datetime import datetime, timedelta
import calendar
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse

@login_required
def admin_event_calendar(request):
    """
    Display and manage events in a calendar view
    """
    # Get all flight groups for the dropdown
    flight_groups = FlightGroup.objects.all()
    
    # Get current year and month (default to current)
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    
    # Get the calendar for the current month
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Get events for the displayed month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Get all events (announcements marked as events)
    events = Announcement.objects.filter(
        is_event=True,
        event_date__gte=start_date,
        event_date__lt=end_date
    ).order_by('event_date')
    
    # Get ALL events for the history section
    all_events = Announcement.objects.filter(is_event=True).order_by('-event_date')
    
    # Format events for the calendar
    event_data = []
    for event in events:
        # Get all flight groups for this event
        event_flight_groups = EventFlightGroup.objects.filter(event=event)
        flight_group_ids = [efg.flight_group.id for efg in event_flight_groups]
        flight_group_names = [efg.flight_group.name for efg in event_flight_groups]
        
        # If no event_flight_groups exist, use the primary flight_group
        if not flight_group_ids and event.flight_group:
            flight_group_ids = [event.flight_group.id]
            flight_group_names = [event.flight_group.name]
        
        event_data.append({
            'id': event.id,
            'title': event.title,
            'date': event.event_date.strftime('%Y-%m-%d'),
            'flight_group': ", ".join(flight_group_names),  # Join all group names
            'flight_group_id': event.flight_group.id if event.flight_group else None,  # Primary group
            'flight_group_ids': flight_group_ids,  # All groups
            'flight_group_names': flight_group_names,  # List of all group names
            'content': event.content
        })
    
    # Calculate previous and next month links
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year = year - 1
        
    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year = year + 1
    
    # Create a dictionary to organize events by flight group
    events_by_group = {}
    for group in flight_groups:
        events_by_group[group.id] = []
    
    # Populate events by group, considering multiple flight groups per event
    for event in all_events:
        # Get all flight groups for this event
        event_flight_groups = EventFlightGroup.objects.filter(event=event)
        
        if event_flight_groups.exists():
            # Add event to each group it belongs to
            for efg in event_flight_groups:
                group_id = efg.flight_group.id
                if group_id in events_by_group:
                    events_by_group[group_id].append(event)
        elif event.flight_group:
            # Fallback to primary flight group
            group_id = event.flight_group.id
            if group_id in events_by_group:
                events_by_group[group_id].append(event)
    
    context = {
        'calendar': cal,
        'month': month,
        'month_name': month_name,
        'year': year,
        'events': event_data,
        'events_json': json.dumps(event_data),
        'flight_groups': flight_groups,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'all_events': all_events,
        'events_by_group': events_by_group,
    }
    
    return render(request, 'admin/admin_event_calendar.html', context)

@login_required
def add_event(request):
    """
    Add a new event to the calendar with multiple flight groups
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        event_date_str = request.POST.get('event_date')
        flight_group_ids = request.POST.getlist('flight_groups[]')  # Note the [] in the name
        
        try:
            # Parse the date
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
            
            # Need at least one flight group
            if not flight_group_ids:
                messages.error(request, 'Please select at least one flight group')
                return redirect('admin_event_calendar')
                
            # Create the announcement (event)
            event = Announcement.objects.create(
                title=title,
                content=content,
                is_event=True,
                event_date=event_date,
                created_by=request.user,
                # Set the first flight group as the primary one (for backward compatibility)
                flight_group=FlightGroup.objects.get(id=flight_group_ids[0])
            )
            
            # Clear any existing flight groups (shouldn't be any for a new event)
            EventFlightGroup.objects.filter(event=event).delete()
            
            # Add all selected flight groups
            for group_id in flight_group_ids:
                flight_group = get_object_or_404(FlightGroup, id=group_id)
                EventFlightGroup.objects.create(
                    event=event,
                    flight_group=flight_group
                )
            
            messages.success(request, 'Event added successfully!')
            
            # Redirect back to the calendar with the appropriate month/year
            return redirect(f'/admin-event-calendar/?year={event_date.year}&month={event_date.month}')
            
        except Exception as e:
            messages.error(request, f'Error adding event: {str(e)}')
    
    # If not POST or error, redirect to calendar
    return redirect('admin_event_calendar')

@login_required
def edit_event(request, event_id):
    """
    Edit an existing event with multiple flight groups
    """
    event = get_object_or_404(Announcement, id=event_id, is_event=True)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        event_date_str = request.POST.get('event_date')
        flight_group_ids = request.POST.getlist('flight_groups[]')  # Note the [] in the name
        
        try:
            # Parse the date
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
            
            # Need at least one flight group
            if not flight_group_ids:
                messages.error(request, 'Please select at least one flight group')
                return redirect('admin_event_calendar')
                
            # Update the event
            event.title = title
            event.content = content
            event.event_date = event_date
            
            # Set the first flight group as the primary one (for backward compatibility)
            event.flight_group = get_object_or_404(FlightGroup, id=flight_group_ids[0])
            event.save()
            
            # Clear existing flight groups and add the new ones
            EventFlightGroup.objects.filter(event=event).delete()
            for group_id in flight_group_ids:
                flight_group = get_object_or_404(FlightGroup, id=group_id)
                EventFlightGroup.objects.create(
                    event=event,
                    flight_group=flight_group
                )
            
            messages.success(request, 'Event updated successfully!')
            
            # Redirect back to the calendar with the appropriate month/year
            return redirect(f'/admin-event-calendar/?year={event_date.year}&month={event_date.month}')
            
        except Exception as e:
            messages.error(request, f'Error updating event: {str(e)}')
    
    # If not POST or error, redirect to calendar
    return redirect('admin_event_calendar')

@login_required
def delete_event(request, event_id):
    """
    Delete an event
    """
    event = get_object_or_404(Announcement, id=event_id, is_event=True)
    
    try:
        # Store date info before deleting for redirect
        year = event.event_date.year
        month = event.event_date.month
        
        # Delete the event
        event.delete()
        
        messages.success(request, 'Event deleted successfully!')
        
        # Redirect back to the calendar with the appropriate month/year
        return redirect(f'/admin-event-calendar/?year={year}&month={month}')
        
    except Exception as e:
        messages.error(request, f'Error deleting event: {str(e)}')
    
    # If error, redirect to calendar
    return redirect('admin_event_calendar')

@login_required
def get_event_details(request, event_id):
    """
    Get event details for AJAX requests
    """
    event = get_object_or_404(Announcement, id=event_id, is_event=True)
    
    data = {
        'id': event.id,
        'title': event.title,
        'content': event.content,
        'date': event.event_date.date().strftime('%Y-%m-%d'),
        'flight_group_id': event.flight_group.id,
        'flight_group_name': event.flight_group.name,
        'created_by': event.created_by.username
    }
    
    return JsonResponse(data)

# Add new view for PDF export
@login_required
def export_events_pdf(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        events = data.get('events', [])
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="event_history.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        
        # Create table data
        table_data = [['Date', 'Title', 'Flight Group', 'Description', 'Created By']]
        for event in events:
            table_data.append([
                event['date'],
                event['title'],
                event['group'],
                event['description'],
                event['creator']
            ])
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return response 