import csv

from django.db.models import Max
from django.utils.translation import ugettext_lazy as _
from urllib2 import URLError
from googlemaps import GoogleMaps, GoogleMapsError
from locations.models import Location
from locations.exceptions import LocationEncodingError


class CsvParseError(csv.Error):
    pass


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    """From Python csv documentation, used to read non-ASCII data"""
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield unicode(line.decode('cp1252')).encode('utf8')


def get_data_list(csv_reader, has_header=False):
    """
    Reads from the csv reader object and creates a list of dictionaries with
    all fo the values, separating csv parsing from all other data management.
    """
    locations_list = []
    # TODO: re-implement this, perhaps after fixing problem of newlines
    # inside strings... the problems look like this (next two rows):
    # "My string starts
    # ", 5, 3
    ##row_start = 1 if csv.Sniffer().has_header(sample) else 0
    # This had to be commented out because the csv reader object is not
    # subscriptable!
    ##for (counter, row) in enumerate(csv_reader[row_start:]):
    for (counter, row) in enumerate(csv_reader):
        # Postal code is optional
        try:
            postal_code = row[4].strip()
        except IndexError:
            postal_code = ''
        try:
            locations_list.append({
                'name': row[0].strip(),
                'address': row[1].strip(),
                'city': row[2].strip(),
                'state': row[3].strip(),
                'postal_code': postal_code,
                })
        except IndexError:
            raise CsvParseError("Missing a column in row %s" % (counter + row))
        except Exception:
            raise CsvParseError(
                    "%s exception in row %s, %s" % (Exception, (counter + row), row))
    return locations_list


def locations_from_csv(csv_file, category, has_header=False,
                                                duplicates_field=None):
    """
    Something something
    """
    sample = csv_file.read(1024)
    dialect = csv.Sniffer().sniff(sample)
    csv_file.seek(0)
    csv_reader = unicode_csv_reader(csv_file, dialect)
    messages = {
            'errors': True,
            'warnings': [],
            'created': [],
            'skipped': [],
            'created_count': 0,
            'skipped_count': 0,
            'upload_count': 0,
    }
    try:
        location_list = get_data_list(csv_reader)
    except CsvParseError, e:
        messages['warnings'].append(e)
        return messages
    counter_query = Location.objects.aggregate(Max('upload_count')).get('upload_count__max', 0)
    upload_counter = 0 if counter_query is None else counter_query + 1
    for location_row in location_list:
        try:
            location, created = Location.objects.get_or_create(
                    original_name=location_row['name'], defaults={
                        'name':  " ".join([word[0].upper() + word[1:].lower() for word in location_row['name'].split()]),
                        'street_address': " ".join([word[0].upper() + word[1:].lower() for word in location_row['address'].split()]),
                        'city': " ".join([word[0].upper() + word[1:].lower() for word in location_row['city'].split()]),
                        'state': location_row['state'].upper(),
                        'postal_code': location_row['postal_code'],
                        'upload_count': upload_counter,
                        })
        except Location.MultipleObjectsReturned:
            messages['warnings'].append(
                    "%s is already duplicated in the database" % location_row['name'])
            created = False
        if created:
            location.category.add(category)
            location.save()
            messages['created'].append(location_row['name'])
        else:
            # Duplicate, but enforce that it is now active
            location.is_active = True
            location.save()
            messages['skipped'].append(location_row['name'])
    messages['errors'] = False
    messages['created_count'] = len(messages['created'])
    messages['skipped_count'] = len(messages['skipped'])
    messages['upload_count'] = upload_counter
    return messages


def geopoint_average(points):
    """Takes a list of lat-lng tuples and returns an average"""
    count = len(points)
    if not count:
        return None
    lat = 0
    lng = 0
    for point in points:
        lat += point[0]
        lng += point[1]
    return (lat/count, lng/count)


def get_address_latlng(location):
    """
    Requests the latitude and longitude for the given location's address.

    Uses the Google Maps API, but could be extended to use a different API.
    """
    address = u"%s, %s, %s %s" % (location.street_address, location.city,
            location.state, location.postal_code)
    try:
        return GoogleMaps().address_to_latlng(address)
    except GoogleMapsError:
        raise LocationEncodingError(_("Google reported an error!"))
    except URLError:
        raise LocationEncodingError(_("Hmm, network error. Please try again."))
    except Exception, e:
        raise LocationEncodingError(_("Unknown error: %s, %s" % (
            Exception, e)))


def geocode_location(location):
    """
    Basically the same as geocode_address but acts on the location.
    """
    location.point = get_address_latlng(location)
    location.save()
    return location
