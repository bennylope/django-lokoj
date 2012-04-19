from django.conf import settings
from django.contrib.localflavor.us.models import USStateField
from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _

from locations.exceptions import PointException
from locations.managers import LocationManager
# Need to import this module somewhere
from locations.filters import NullableFieldFilterSpec


class LocationCategory(models.Model):
    """
    Stores the categories of locations
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    class Meta:
        verbose_name = "Location category"
        verbose_name_plural = "Location categories"

    def __unicode__(self):
        return u"%s" % self.name


class Location(models.Model):
    """
    A model class for managing locations, whatever they may represent.
    """
    category = models.ManyToManyField(LocationCategory)
    original_name = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100,
            help_text="The display name")
    street_address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=100)
    state = USStateField()
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    latitude = models.DecimalField(decimal_places=15, max_digits=18, null=True,
            blank=True)
    longitude = models.DecimalField(decimal_places=15, max_digits=18, null=True,
            blank=True)
    url = models.URLField(verify_exists=False, blank=True,
            help_text="An optional link for this location")
    description = models.TextField(blank=True,
            help_text="An optional description for this location")
    is_active = models.BooleanField(default=True)
    upload_count = models.IntegerField(default=0)

    objects = LocationManager()

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u"%s" % self.name

    def save(self, *args, **kwargs):
        return super(Location, self).save(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return ('location_detail', (), {
            'pk': self.pk
        })

    def _get_point(self):
        return self.latitude, self.longitude

    def _set_point(self, point_tuple):
        """
        Method to set the latitude and longitude via a single tuple or list.
        The method verifies the data types right away, rather than just wait
        for the model's `save` method to clean the data.
        """
        try:
            assert len(point_tuple) == 2
        except AssertionError:
            raise PointException("point_tuple must have exactly two elements")
        try:
            assert (isinstance(point_tuple[0], int) or \
                    isinstance(point_tuple[0], float)) and \
                    (isinstance(point_tuple[1], int) or \
                    isinstance(point_tuple[1], float))
        except AssertionError:
            raise TypeError("point_tuple elements must be numeric")
        # Force to byte string b/c Python 2.6 Decimal class cannot convert from
        # float values, throws "Cannot convert float to Decimal" exception.
        self.latitude = str(point_tuple[0])
        self.longitude = str(point_tuple[1])
        return self.latitude, self.longitude

    point = property(_get_point, _set_point)

    def float_point(self):
        if self.latitude and self.longitude:
            return float(self.latitude), float(self.longitude)
        else:
            return None

    @property
    def has_geolocation(self):
        if self.latitude is not None and self.longitude is not None:
            return True
        else:
            return False

    # This adds the custom filterspec to the latitude field to filter locations
    # that have some geocoding.
    latitude.got_geocoding = True
    state.filter_state = 'All'

    def admin_geolocation(self):
        """
        This method adds a custom column to the admin interface to display an
        icon identifying whether this location has geodata.
        """
        if self.has_geolocation:
            return u"<img src='%s%s'>" % (settings.STATIC_URL,
                    'locations/green-globe.png')
        else:
            return u"<img src='%s%s'>" % (settings.STATIC_URL,
                    'admin/img/admin/icon-no.gif')
    admin_geolocation.short_description = 'Geolocated?'
    admin_geolocation.allow_tags = True

    def location(self):
        """
        This method does nothing but return the name of the object. It comes in
        handy in the admin view, when it's convenient to use the name of the
        object as the link to the object's edit page and simultaneously
        exposing the name as list editable. It uses the original name - which
        is critical when uploading or adding via the management command - as
        this may be more descriptive than the `name` field, which is a display
        field.
        """
        return u"%s" % self.original_name if self.original_name else u"%s" % self.name
