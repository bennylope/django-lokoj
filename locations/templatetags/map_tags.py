from django import template

register = template.Library()


@register.simple_tag
def google_maps_url(location):
    """
    Parses together a google map link
    """
    url = u"http://maps.google.com/maps?"
    url = u"%sq=%s+%s+%s+%s+%s" % (url, location.name, location.street_address,
            location.city, location.state, location.postal_code)
    if location.has_geolocation:
        url = u"%s&amp;sll=%s,%s" % (url, location.latitude, location.longitude)
    return url.replace(" ", "+")
