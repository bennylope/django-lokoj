Django-Lokoj: Locations Management
==================================

Allows you to add locations of different types to a Django project and geocode
their locations for basic geographic searches.

Have multiple locations for offices, stores, products, vendors, campuses,
chapters, affiliates, or something in between? This is the app for you.

Requirements
------------

* Django
* django-google-maps
* `django-postalcodes <http://github.com/bennylope/django-postalcodes>`_


Install
-------

Clone the repository and add it to your Python path. Then add the requisite
applications to your `INSTALLED_APPS` list::

    INSTALLED_APPS = (
        ....
        'postalcodes',
        'django_google_maps',
        'locations',
    )

If you are using Django-CMS you can install the `locations_cms` application to
use the app hook::

    INSTALLED_APPS = (
        ....
        'postalcodes',
        'django_google_maps',
        'locations',
        'locations.locations_cms',
    )
