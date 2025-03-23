from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using the key
    """
    return dictionary.get(key, [])

@register.filter
def filter_by_gender(students, gender):
    """
    Filter a list of students by gender
    """
    return [student for student in students if student.gender == gender] 