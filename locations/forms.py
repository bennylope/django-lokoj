from decimal import InvalidOperation

from django import forms
from django.utils.translation import ugettext as _

from django_google_maps.widgets import GoogleMapsAddressWidget
from locations.models import Location, LocationCategory


class LocationSearchForm(forms.Form):
    """
    A form to collect and validate location search/filter data

    The geo query and the distance are both optional fields, but the limit
    should not be present without the geo_query.
    """
    state = forms.ChoiceField(required=False,
            choices=Location.objects.state_choices(),
            widget=forms.CheckboxSelectMultiple)
    category = forms.ModelMultipleChoiceField(required=False,
            help_text="Limit your search by establishment type",
            label="Beer Sold in",
            queryset=LocationCategory.objects.all(),
            widget=forms.CheckboxSelectMultiple)
    search = forms.CharField(max_length=50, required=False,
            help_text="Search by name",
            label="Name")
    geo_query = forms.CharField(max_length=5, required=False,
            help_text="Search by 5 digit zip code",
            label="Zip Code")

    def clean_geo_query(self):
        """Only allow 5-digit zip codes for now"""
        geo_query = self.cleaned_data["geo_query"]
        if not geo_query:
            return geo_query
        try:
            int(geo_query)
        except:
            raise forms.ValidationError("Enter a 5-digit zipcode")
        if len(geo_query) != 5:
            raise forms.ValidationError("Enter a 5-digit zipcode")
        return geo_query


class LocationAdminForm(forms.ModelForm):
    """
    A form for updating individual locations in the admin. It allows us to use
    one text input field for reading and populating the latitude and longitude
    fields, which are each stored as individual decimal fields. Decimal fields
    in the database are much better for fast numeric queries, but totally
    unnecessary for human reading and editing.

    The GoogleMapsAddressWidget does not, despite its name, depend on an
    address field. All it does is render a text input and append the div
    wrapper for the Google Map.
    """
    geolocation = forms.CharField(max_length=100, required=False,
        widget=GoogleMapsAddressWidget,
        help_text="Latitude and longitude, e.g. (-90.801, 108.123)")

    class Meta:
        model = Location
        exclude = ('latitude', 'longitude')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        if instance:
            if instance.latitude and instance.longitude:
                initial['geolocation'] = u"%s,%s" % (instance.latitude, instance.longitude)
        kwargs['initial'] = initial
        super(LocationAdminForm, self).__init__(*args, **kwargs)

    def clean_geolocation(self):
        """
        Ensure that the latitude and longitude comply with the respective
        model field constraints.
        """
        geolocation = self.cleaned_data.get('geolocation', '').strip()
        if not geolocation:
            return geolocation
        else:
            try:
                lat, lng = [float(val.strip()) for val in geolocation.split(",")]
            except ValueError:
                raise forms.ValidationError(
                    "You must enter two numeric values for latitude and longitude")
            try:
                return u"%s,%s" % (round(lat,15), round(lng,15))
            except TypeError:
                raise forms.ValidationError(
                    "You must enter numeric values only")

    def save(self, commit=True):
        """
        Make sure to parse the geolocation
        """
        # TODO: remove redundnacy, have this rely solely on cleaning method to
        # get the pieces
        geolocation = self.cleaned_data.get('geolocation')
        if not geolocation:
            pieces = (None, None)
        else:
            try:
                pieces = [float(x) for x in geolocation.split(",")]
            except ValueError:
                raise ValueError("Latitude and longitude must be numeric values")
            except InvalidOperation:
                raise InvalidOperation("Latitude or longitude have too many digits")
        self.instance.latitude = pieces[0]
        self.instance.longitude = pieces[1]
        return super(LocationAdminForm, self).save(commit)


class CsvUploadForm(forms.Form):
    """
    This form is used to input and process a CSV file with locations.
    """
    category = forms.ModelChoiceField(LocationCategory.objects.all(),
        label=_("Location category"),
        help_text=_("This will be applied to all new locations."))
    csv_file = forms.FileField(label=_("CSV file"))
