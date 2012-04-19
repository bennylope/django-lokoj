from django.conf.urls.defaults import patterns, url
from django.views.generic import DetailView

from locations.models import Location
from locations.views import LocationListView, LocationKMLFeed


urlpatterns = patterns('',
    url(r'^$',
        view=LocationListView.as_view(
            template_name="locations/location_index.html",
            paginate_by=24,
        ), name="location_index"),
    url(r'^search/$', view=LocationListView.as_view(), name="location_list"),
    url(r'^locations.kml$', view=LocationKMLFeed.as_view(), name="location_kml"),
    url(r'^(?P<pk>[\d]+)/$',
        view=DetailView.as_view(queryset=Location.objects.public(),
        context_object_name="location"), name="location_detail"),
)
