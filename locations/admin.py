from django.contrib import admin
from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import permission_required
from django.utils.translation import ugettext as _

from locations.models import Location, LocationCategory
from locations.views import CsvUpload
from locations.exceptions import LocationEncodingError
from locations.utils import geocode_location
from locations.forms import LocationAdminForm


class LocationCategoryAdmin(admin.ModelAdmin):
    """
    Admin for the Location Category model
    """
    pass


class LocationAdmin(admin.ModelAdmin):
    """
    Admin for the Location model
    """
    # TODO: after adding in the geolocation functionality, add an admin action
    # to regenerate the lat/long data for selected locations
    form = LocationAdminForm
    list_display = ('location', 'name', 'street_address', 'city', 'state',
            'postal_code', 'is_active', 'admin_geolocation')
    #list_editable = ['name', ]
    list_filter = ('category', 'is_active', 'latitude', 'state')
    search_fields = ['name', 'street_address', 'city']
    save_on_top = True
    fieldsets = (
            (None, {
                'fields': ('name', 'category', 'is_active'),
                }),
            ('Address', {
                'fields': ('street_address', 'city', 'state', 'postal_code'),
                }),
            ('Geolocation', {
                'fields': ('geolocation',),
                #'classes': ('collapse',),
                }),
            ('Additional information', {
                'fields': ('description', 'url'),
                'classes': ('collapse',),
                }),
            )

    actions = ['geocode_address', 'toggle_active_status']

    def geocode_address(self, request, queryset):
        """
        Make a request from Google via the Maps API to get the lat/lng
        locations for the selected locations.
        """
        msg = ""
        if len(queryset) > 10:
            queryset = queryset[:10]
            msg = _(" Only 10 locations can be geocoded at a time.")
        try:
            rows_updated = map(geocode_location, queryset)
        except LocationEncodingError:
            rows_updated = []
            self.message_user(request, "There was an error")
        total_updated = len(rows_updated)
        if total_updated == 1:
            message_bit = _("The %(location)s location was" % {
                'location': rows_updated[0]})
        else:
            message_bit = _("%(count)s locations were" % {
                'count': total_updated})
        self.message_user(request, "%(message)s successfully geocoded.%(followup)s" % {
            'message': message_bit, 'followup': msg})

    def toggle_active_status(self, request, queryset):
        """
        Makes the status of each selected location the opposite of its current
        status
        """
        active_count = 0
        inactive_count = 0
        for location in queryset:
            location.is_active = not location.is_active
            if location.is_active:
                active_count += 1
            else:
                inactive_count += 1
            location.save()
        self.message_user(request,
            "%(active)s locations made active, %(inactive)s locations made inactive." % {
                'active': active_count, 'inactive': inactive_count})

    def get_urls(self):
        urls = super(LocationAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^upload_csv/$',
                view=permission_required('locations.add_location')(CsvUpload.as_view()),
                #view=self.admin_site.admin_view(CsvUpload.as_view()),
                name="location_csv_upload"
            )
        )
        return my_urls + urls


admin.site.register(LocationCategory, LocationCategoryAdmin)
admin.site.register(Location, LocationAdmin)
