"""
Custom template tags for displaying star ratings.
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def star_rating(rating):
    """
    Generates the HTML for a star rating display.
    """
    if rating is None:
        return ""

    try:
        rating = float(rating)
    except (ValueError, TypeError):
        return ""

    full_stars = int(rating)
    has_half_star = (rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if has_half_star else 0)

    stars_html = []
    for _ in range(full_stars):
        stars_html.append('<i class="fas fa-star"></i>')

    if has_half_star:
        stars_html.append('<i class="fas fa-star-half-alt"></i>')

    for _ in range(empty_stars):
        stars_html.append('<i class="far fa-star"></i>') # Using far for empty stars

    return mark_safe("".join(stars_html))
