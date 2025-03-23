from django import template
from myapp.models import FlightGroup

register = template.Library()

@register.filter
def get_flight_group_name(flight_group_id):
    """Get the name of a flight group from its ID"""
    try:
        return FlightGroup.objects.get(id=flight_group_id).name
    except FlightGroup.DoesNotExist:
        return "Not Assigned"

@register.filter
def get_flight_group_members(flight_group_id):
    """Get the count of personnel in a flight group"""
    try:
        flight_group = FlightGroup.objects.get(id=flight_group_id)
        return flight_group.personnel_set.count()
    except FlightGroup.DoesNotExist:
        return 0 