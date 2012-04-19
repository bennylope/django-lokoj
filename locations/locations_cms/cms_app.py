from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _


class LocationsApphook(CMSApp):
    name = _("Locations")
    urls = ["locations.urls"]


apphook_pool.register(LocationsApphook)

