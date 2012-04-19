from django.contrib import messages
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson as json
from django.views.generic import TemplateView, ListView, FormView

from locations.models import Location
from locations.forms import CsvUploadForm, LocationSearchForm
from locations.utils import locations_from_csv


class LocationListView(ListView):
    """
    A view to list and search available locations. It allows filtering by:

        * City
        * State
        * Zip code
        * Category of location

    It allows searching by:

        * Name query
        * Zip code (proximity)
        * Lat/lng (proximity)

    It also provides the results in JSON if that format is specified.

    """
    context_object_name = 'locations'

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.

        The pagination parameter must be a positive integer
        """
        paginate = self.request.REQUEST.get('paginate_by')
        # Make sure it's not 'None'
        paginate = paginate if paginate else self.paginate_by
        # Make sure it's a numeric value
        try:
            paginate = int(paginate)
        except (TypeError, ValueError):
            paginate = self.paginate_by
        if paginate < 1:
            paginate = self.paginate_by
        return paginate

    def get_context_data(self, **kwargs):
        context = super(LocationListView, self).get_context_data(**kwargs)
        url_params = kwargs.get('query_dict', {})
        context["form"] = LocationSearchForm(initial=url_params)
        url_params = url_params.copy() # Make it mutable
        url_params.pop('page', None) # Get rid of any page references
        context["url_params"] = url_params.urlencode()
        return context

    def get_queryset(self, querydict, **kwargs):
        """
        Get the list of items for this view. This must be an interable, and may
        be a queryset (in which qs-specific behavior will be enabled).
        """
        queryset = Location.objects.public()
        geo_query = querydict.get('geo_query', None) # used for zip and lat/lng
        city_filter = querydict.get('city', None)
        state_filter = querydict.getlist('state')
        postal_filter = querydict.getlist('postcode')
        category_filter = querydict.getlist('category')
        search_query = querydict.get('search', None)
        direction = querydict.get('direction', '')
        sort = querydict.get('sort', None)
        limit = querydict.get('limit', None)
        if geo_query:
            queryset = Location.objects.geosearch(geo_query).filter(is_active=True)
            sort = 'distance' if not sort else 'name'
        if city_filter:
            queryset = queryset.filter(city=city_filter)
        if state_filter:
            queryset = queryset.filter(state__in=state_filter)
        if postal_filter:
            queryset = queryset.filter(postal_code__in=postal_filter)
        if search_query:
            queryset = queryset.filter(Q(Q(name__icontains=search_query) |
                    Q(street_address__icontains=search_query) |
                    Q(city__icontains=search_query)))
        if category_filter:
            queryset = queryset.filter(category__id__in=category_filter)
        try:
            limit = int(limit)
        except TypeError:
            # [:None] evaluates to the entire list
            limit = None
        sort = sort if sort else 'name'
        queryset = queryset.select_related('category')
        # Make sure we do not try to sort distance outside of the select extra,
        # otherwise we'll get an error about trying to sort on a non-existent
        # field, since this sort only sorts on defined database fields
        if sort != 'distance':
            queryset = queryset.order_by("%s%s" % (direction, sort))
        return queryset.distinct()[:limit]

    def is_ajax_request(self, request):
        """
        Returns true if the request is made by XMLHttpRequest or explictly
        requests the response in JSON format.
        """
        if request.GET.get(u"format", "html").lower() == u"json" or request.is_ajax():
            return True
        return False

    def get(self, request, *args, **kwargs):
        use_json = self.is_ajax_request(request)
        self.object_list = self.get_queryset(request.GET, **kwargs)
        context = self.get_context_data(object_list=self.object_list,
                query_dict=request.GET)
        if use_json:
            locations = [{
                "id": location.id,
                "name": location.name,
                "street_address": location.street_address,
                "city": location.city,
                "postal_code": location.postal_code,
                "categories": [{
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    } for category in location.category.all()],
                "distance": getattr(location, 'distance', None),
                "latlng": location.float_point(),
                } for location in self.object_list]
            response = HttpResponse(content_type="application/json")
            response.content = json.dumps(locations)
            return response
        else:
            return self.render_to_response(context)


class LocationKMLFeed(ListView):
    """
    A very simplified version of a GeoRSS feed
    """
    queryset = Location.objects.geocoded()
    context_object_name = 'locations'
    template_name = "locations/location_list.xml"

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list)
        return self.render_to_response(context,
                **{'content_type':"application/vnd.google-earth.kml+xml"})


class LocationGeoSitemap(TemplateView):
    """
    Serves a very simple geo site map to satisfy Google's requirements:

    http://code.google.com/apis/kml/documentation/kmlSearch.html

    The sitemap URL must be installed in the root URL conf so that it can be
    served from the site root.
    """
    template_name = 'locations/geo_sitemap.xml'

    def get_context_data(self, **kwargs):
        from django.contrib.sites.models import Site
        return {
            'site': Site.objects.get_current(),
            'url': reverse('location_kml'),
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context,
                **{'content_type':'application/xml'})


class CsvUpload(FormView):
    """
    A view class used in the admin area to upload and process a CSV file with
    locations.
    """
    # TODO: make sure that the context knows that this is part of the Locations
    # application
    # TODO: add a message for successful loading of all new locations
    template_name = "admin/locations/admin_csv_upload.html"
    form_class = CsvUploadForm

    def get_context_data(self, **kwargs):
        context = super(CsvUpload, self).get_context_data(**kwargs)
        # These context items are for the admin templates
        context['cl'] = Location
        context['title'] = u"Batch locations upload"
        context['opts'] = {}
        context['change'] = True # ??
        context['save_as'] = False ## ??
        context['is_popup'] = False
        return context

    def get_success_url(self):
        # TODO: at the least go to the changelist showing only the most
        # recently uploaded items
        return reverse("admin:locations_location_changelist")

    def form_valid(self, request, form):
        """
        Sends the csv file to be processed
        """
        # probably needs to make a stringio object out of it
        csv_file = form.cleaned_data['csv_file']
        category = form.cleaned_data['category']
        csv_results = locations_from_csv(csv_file, category)
        if csv_results['errors']:
            messages.add_message(request, messages.ERROR, 'There was an error.')
        else:
            if csv_results['created_count']:
                messages.add_message(request, messages.SUCCESS,
                        "%s new locations added" % csv_results['created_count'])
            if csv_results['skipped_count']:
                messages.add_message(request, messages.WARNING,
                        "%s duplicates skipped" % csv_results['skipped_count'])
        if "_edit" in request.POST:
            if csv_results['created_count'] == 0:
                messages.add_message(request, messages.WARNING,
                        "There are no new locations to edit")
            return HttpResponseRedirect('%s?upload_count=%s' % (
                self.get_success_url(), (csv_results['upload_count'])))
        return self.render_to_response(self.get_context_data(
                form=form, csv_results=csv_results))

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        """
        Re-implemented to send the request object to the form_valid method.
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(request, form)
        else:
            return self.form_invalid(form)
