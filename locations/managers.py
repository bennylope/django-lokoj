import logging

from django.db import models
from django.db.models import Q

from postalcodes.models import PostalCode


def get_multiple_ids_string(queryset):
    """Returns a string of ids from a queryset for use in a SQL query"""
    querystring = ""
    for counter, modobj in enumerate(queryset):
        querystring += ", %s" % modobj.id if counter > 0 else "%s" % modobj.id
    return querystring


class LocationManager(models.Manager):
    """
    Manager class for Location objects.
    """

    def public(self):
        """Returns only locations which are marked as available"""
        return super(LocationManager, self).get_query_set().filter(is_active=True)

    def geocodeable(self):
        """Returns only locations with addresses that can be geocoded"""
        return super(LocationManager, self).get_query_set().filter(
                ~Q(street_address=None), ~Q(street_address=''))

    def geocoded(self):
        """
        Returns all publicly visible locations with geocoding
        """
        return self.public().filter(~Q(latitude=None))

    def state_choices(self):
        """
        Returns a tuple of tuples ((x,y), (a,b)) with the distinct state values
        and full names for active locations.
        """
        from django.contrib.localflavor.us.us_states import STATE_CHOICES
        state_names = dict(STATE_CHOICES)
        states = self.public().values('state')
        state_vals = list(set([state['state'].upper() for state in states]))
        state_vals.sort()
        return tuple([(state_val, state_names[state_val]) for state_val in state_vals])

    def geosearch(self, query):
        """
        Returns a queryset sorted by geographic proximity to the query.

        The geosearch method depends on a raw query, so it must sanitize all
        its inputs without relying on Django to protect from SQL injection
        attacks.

        :param query: The location against which to search, either represents
            a postal code or latitude and longitude
        :type query: Either a string or a tuple
        """
        try:
            latitude, longitude = query.split(',')
        except ValueError:
            # Possibly a zip code?
            postal_code = query[:5]
            try:
                postal_area = PostalCode.objects.get(code=postal_code)
            except PostalCode.DoesNotExist:
                # No such postal code, dolts!
                # TODO: there should be a warning somewhere about this, perhaps
                # a message sent to the user?
                return self.get_query_set().all()
            else:
                latitude, longitude = postal_area.latitude, postal_area.longitude
        else:
            latitude, longitude = float(latitude), float(longitude)
        return self.distance(latitude, longitude)

    def distance(self, latitude, longitude):
        """
        Returns a QuerySet of locations annotated with their distance from the
        given point.

        It implements the Haversine formula.

        Coefficients represent great cirlce measurements. Options include
            3956 - miles
            6371 - kilometers

        http://www.benamy.info/guides/haversine-formula-distance-query-with-django-postgresql

        Trying this on Sqlite will yield a DatabaseError exception

        """
        # TODO: tests for type on latitude, longitude as well as database
        # This is returning a queryset but not a queryset that can be iterated
        # over until it's been coerced into a list
        coefficient = 3959
        return self.get_query_set().extra(select={
            "distance": "%s * acos(cos(radians(%s)) * cos(radians(latitude)) "
                        "* cos(radians(longitude) - radians(%s)) + "
                        "sin(radians(%s)) * sin(radians(latitude)))"},
                select_params=(coefficient, latitude, longitude,
                    latitude)).order_by('distance')

