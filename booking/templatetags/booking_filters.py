from django import template
import jdatetime
import pytz

register = template.Library()

@register.filter(name='to_jalali_js')
def to_jalali_js(gregorian_date):
    """
    Converts a Gregorian date to a Jalali date string in 'YYYY/MM/DD' format for JS.
    """
    if not gregorian_date:
        return ""
    if hasattr(gregorian_date, 'date'):
        gregorian_date = gregorian_date.date()
    try:
        j_date = jdatetime.date.fromgregorian(date=gregorian_date)
        return f"{j_date.year}/{j_date.month}/{j_date.day}"
    except (ValueError, TypeError):
        return gregorian_date

@register.filter(name='to_jalali_date')
def to_jalali_date(gregorian_date):
    """
    Converts a Gregorian datetime object to a Jalali date string.
    """
    if not gregorian_date:
        return ""
    try:
        j_date = jdatetime.date.fromgregorian(date=gregorian_date)
        return f"{j_date.year}/{j_date.month}/{j_date.day}"
    except (ValueError, TypeError):
        return gregorian_date

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

        jalali_day_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        jalali_month_names = [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]

        result = format_str
        result = result.replace('%Y', str(jalali_date.year))
        result = result.replace('%m', f'{jalali_date.month:02d}')
        result = result.replace('%d', f'{jalali_date.day:02d}')

        if '%A' in result:
            result = result.replace('%A', jalali_day_names[jalali_date.weekday()])

        if '%B' in result:
            result = result.replace('%B', jalali_month_names[jalali_date.month - 1])

        return result
    except (ValueError, TypeError):
        return gregorian_date

@register.filter(name='to_jalali_datetime')
def to_jalali_datetime(gregorian_datetime, format_str="%A %Y/%m/%d, ساعت %H:%M"):
    """
    Converts a Gregorian datetime object to a Jalali datetime string.
    Example usage: {{ my_datetime|to_jalali_datetime }}
    Or with format: {{ my_datetime|to_jalali_datetime:"%A, %d %B %Y - %H:%M" }}
    """
    if not gregorian_datetime:
        return ""
    try:
        # Convert to the 'Asia/Tehran' timezone

        tehran_tz = pytz.timezone('Asia/Tehran')
        if gregorian_datetime.tzinfo is None:
            gregorian_datetime = pytz.utc.localize(gregorian_datetime)

        local_datetime = gregorian_datetime.astimezone(tehran_tz)
        jalali_datetime = jdatetime.datetime.fromgregorian(datetime=local_datetime)

        jalali_day_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        jalali_month_names = [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]

        result = format_str
        result = result.replace('%Y', str(jalali_datetime.year))
        result = result.replace('%m', f'{jalali_datetime.month:02d}')
        result = result.replace('%d', f'{jalali_datetime.day:02d}')
        result = result.replace('%H', f'{jalali_datetime.hour:02d}')
        result = result.replace('%M', f'{jalali_datetime.minute:02d}')

        if '%A' in result:
            result = result.replace('%A', jalali_day_names[jalali_datetime.weekday()])

        if '%B' in result:
            result = result.replace('%B', jalali_month_names[jalali_datetime.month - 1])

        return result
    except (ValueError, TypeError):
        return gregorian_datetime

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
@register.filter(name='comma')
def comma(value):
    try:
        # تبدیل به عدد
        value = float(value)  # یا int(value) بر حسب نیاز 
        # فرمت کردن عدد با کاما
        return f"{value:,.0f}"  # صفر برای نمایش بدون اعشار
    except (ValueError, TypeError):
        return value  # اگر خطایی ایجاد شد، مقدار اصلی را برگردانید

@register.filter(name='div')
def div(value, arg):
    """
    Divides the value by the arg.
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter(name='to_persian_weekday')
def to_persian_weekday(gregorian_date):
    """
    Converts a Gregorian date object to a Persian weekday name.
    """
    if not gregorian_date:
        return ""

    if hasattr(gregorian_date, 'date'):
        gregorian_date = gregorian_date.date()

    try:
        jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
        weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        return weekdays[jalali_date.weekday()]
    except (ValueError, TypeError):
        return ""

@register.filter(name='split')
def split(value, arg):
    """
    Splits the value by the arg.
    """
    if value:
        return value.split(arg)
    return []
