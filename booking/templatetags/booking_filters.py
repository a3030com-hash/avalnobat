from django import template
import jdatetime

register = template.Library()

@register.filter(name='to_jalali')
def to_jalali(gregorian_date, format_str="%Y/%m/%d"):
    """
    Converts a Gregorian date object to a Jalali date string.
    Example usage: {{ my_date|to_jalali }}
    Or with format: {{ my_date|to_jalali:"%A, %d %B %Y" }}
    """
    if not gregorian_date:
        return ""

    # If it's a datetime object, convert to date first
    if hasattr(gregorian_date, 'date'):
        gregorian_date = gregorian_date.date()

    try:
        jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
        return jalali_date.strftime(format_str)
    except (ValueError, TypeError):
        return gregorian_date

@register.filter(name='intcomma')
def intcomma(value):
    """
    Converts an integer to a string containing commas every three digits.
    """
    try:
        value = int(value)
        return f"{value:,}"
    except (ValueError, TypeError):
        return value

@register.filter(name='div')
def div(value, arg):
    """
    Divides the value by the arg.
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None