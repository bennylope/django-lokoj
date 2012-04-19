from django import template
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http import QueryDict

from locations.forms import LocationSearchForm
from locations.models import LocationCategory, Location
from locations.views import LocationListView

# Test managers
# Test geocoding - mock?
# Test basic views

# DO NOT test the geoquery method just yet - may be removed in favor of having
# a postalcodes view that returns lat/long via javascript to the form

# TODO: control how any tests regarding the "distance" manager method are run,
# since they require PostgreSQL and cannot be run in SQLite

class LocationManagersTest(TestCase):
    """
    Make sure the custom manager methods return quersets limited and ordered in
    the correct way.
    """
    fixtures = ["test_data.json"]

    def setUp(self):
        pass

    def test_public(self):
        self.assertEqual(Location.objects.public().count(), 11)

    def test_geocoded(self):
        self.assertEqual(Location.objects.geocoded().count(), 10)

    def test_distance(self):
        """Ensure that all locations returned, ascending order"""
        locations = Location.objects.distance(38.863504,-77.058835)
        self.assertEqual(len(locations), 12)
        self.assertFalse(locations[11].distance) # Last one is not geocoded
        for counter in range(10):
            self.assertTrue(
                    locations[counter].distance < locations[counter + 1])

    def test_state_tuple(self):
        """Ensure that returns tuple of state choices from active locations"""
        choices = (
                (u'AK', 'Alaska'),
                (u'DC', 'District of Columbia'),
                (u'IL', 'Illinois'),
                (u'LA', 'Louisiana'),
                (u'MD', 'Maryland'),
                (u'VA', 'Virginia'),
            )
        self.assertEqual(Location.objects.state_choices(), choices)

    def test_is_geocodeable(self):
        """Ensure that the manager returns only locations with street address"""
        new_loc = Location.objects.create(name="No address", city="Nowhere",
                state="VA")
        self.assertEqual(13, Location.objects.all().count())
        self.assertEqual(12, Location.objects.geocodeable().count())


class LocationSearchFormTest(TestCase):
    """
    The search form allows users to find locations by filtering on categories,
    searching on names, and searching by location.
    """
    fixtures = ["test_data.json"]

    def setUp(self):
        pass

    def test_blank_form_valid(self):
        """Ensure blank forms are valid"""
        form = LocationSearchForm({})
        self.assertTrue(form.is_valid())

    def test_location_geolocation(self):
        """Ensure that a lat/lng pair can be searched to order locations"""
        pass

    def test_postal_code_validation(self):
        """Ensure that postal codes are validated"""
        form = LocationSearchForm({"geo_query": "22202"})
        self.assertTrue(form.is_valid())
        form = LocationSearchForm({"geo_query": "2202"})
        self.assertFalse(form.is_valid())
        form = LocationSearchForm({"geo_query": "22a02"})
        self.assertFalse(form.is_valid())
        form = LocationSearchForm({"geo_query": "220222"})
        self.assertFalse(form.is_valid())



class LocationSearchQuerysetTest(TestCase):
    fixtures = ["test_data.json"]

    def setUp(self):
        self.view = LocationListView()

    def test_empty_queryset(self):
        """Ensure that an empty queryset results in full public search"""
        qs = QueryDict("")
        queryset = self.view.get_queryset(qs)
        self.assertEqual(len(queryset), 11)

    def test_simple_name_search(self):
        """Ensure a basic search matching a name returns the location"""
        qs = QueryDict("search=Pooch")
        queryset = self.view.get_queryset(qs)
        self.assertEqual(len(queryset), 1)

    def test_search_matching_city(self):
        """Ensure a search matching city name(s) returns the locations"""
        qs = QueryDict("search=Arlington")
        queryset = self.view.get_queryset(qs)
        self.assertEqual(len(queryset), 2)

    def test_single_category(self):
        """Ensure that filtering by category returns limited locations"""
        restaurant = LocationCategory.objects.get(name="Restaurant")
        qs = QueryDict("category=%s" % restaurant.id)
        queryset = self.view.get_queryset(qs)
        self.assertEqual(len(queryset), 4)

    def test_multiple_categories(self):
        """Ensure that filtering by multiple categories returns locations"""
        categories = "&".join(
                ["category=%s" % category.id for category in LocationCategory.objects.all()])
        qs = QueryDict(categories)
        queryset = self.view.get_queryset(qs)
        self.assertEqual(len(queryset), 11)

    def test_filter_postal_code(self):
        """Ensure that postal code can be filtered"""
        qs = QueryDict("postcode=22205&postcode=22150")
        queryset = self.view.get_queryset(qs)
        self.assertEqual(len(queryset), 3)

    def test_filter_state(self):
        """Ensure that the state can be filtered"""
        qs = QueryDict("state=AK&state=IL")
        queryset = self.view.get_queryset(qs)
        self.assertEqual(len(queryset), 2)

    def test_json_format(self):
        """Ensure that a request for JSON sends back a JSON response"""
        response = self.client.get("%s?format=json" % reverse("location_list"))
        self.assertEqual(response["Content-Type"], "application/json")

    def test_json_request(self):
        """Ensure ajax request always gets JSON"""
        response = self.client.get(reverse("location_list"),
                **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(response["Content-Type"], "application/json")

    def test_results_limit(self):
        """Ensure results can be limited"""
        qs = QueryDict("limit=5")
        queryset = self.view.get_queryset(qs)
        self.assertEqual(len(queryset), 5)


class LocationListTest(TestCase):
    """
    The List view is basically like the search view, but includes pagination
    """
    fixtures = ["test_data.json"]

    def test_view_exists(self):
        pass
        #url = reverse("location_list")
        #response = self.client.get(url)
        #self.assertEqual(response.status_code, 200)

    def test_paginated_view(self):
        """Ensure that the result set is paginated"""
        pass


class GeoDataTest(TestCase):
    """
    A simplified GeoRSS feed is presented, without reliance on a geospatial
    enabled database or GeoDjango.
    """
    fixtures = ["test_data.json"]

    def test_kml(self):
        response = self.client.get(reverse("location_kml"))
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/vnd.google-earth.kml+xml", response['CONTENT-TYPE'])

    def test_sitemap(self):
        response = self.client.get(reverse("location_sitemap"))
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/xml", response['CONTENT-TYPE'])


class MapTagTest(TestCase):
    """
    Ensure that the google maps template tag loads and works correctly
    """
    def setUp(self):
        self.loc_full = Location.objects.create(
                name="Bob's Place",
                street_address="1600 Pennsylvania Ava",
                city="Washington",
                state="DC",
                postal_code="20500")
        self.loc_partial = Location.objects.create(
                name="Zim's Place",
                street_address="",
                city="Washington",
                state="DC")

    def test_library_loads(self):
        """Ensure the tag library loads without error"""
        t = template.Template("{% load map_tags %}")
        context = template.Context({})
        t.render(context)

    def test_tag_url(self):
        t = template.Template("{% load map_tags %}{% google_maps_url loc %}")
        context = template.Context({'loc': self.loc_full})
        t.render(context)
