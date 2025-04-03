from django import template
from myapp.models import Announcement

register = template.Library()

@register.filter
def get_event_object(event_id):
    """Get the event object from its ID"""
    try:
        return Announcement.objects.get(id=event_id)
    except Announcement.DoesNotExist:
        return None

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    return dictionary.get(key, [])

@register.filter
def filter_events_by_date(events, date):
    return [event for event in events if event['date'] == date] 