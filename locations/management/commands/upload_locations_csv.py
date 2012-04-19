from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from locations.models import LocationCategory, Location
from locations.utils import locations_from_csv


class Command(BaseCommand):
    """
    The upload_locations_csv management command allows a user with shell access
    to upload a file with new locations in comma separated values format. The
    command will - using helper functions available to the rest of the app -
    parse the file and create and/or update existing location entries. Location
    categories cannot be updated via the command.

    Locations are added like so:

        > ./manage.py upload_locations_csv --options filename.csv

    The command should allow the user to pick an initial category to assign to
    the new locations. It should add the location name to the `original_name`
    field in the Location model, and if it is a new Location, add that name to
    the `name` field.
    """
    # TODO: make an option to allow picking the category and skip prompt
    # TODO: make an option to match existing locations based on certain fields
    help = """
        Upload new locations and batch update existing locations from a
        CSV file upload.
        """
    args = u"<file_path>"
    option_list = BaseCommand.option_list + (
            make_option('--duplicates_field',
                action='store',
                dest='duplicates_field',
                default='original_name',
                help="""Field to use for checking duplicates
                        Default is 'original_name'"""),
            make_option('--header',
                action='store_true',
                dest='has_header',
                default=False,
                help="""Does this CSV file have a header row?
                        Default is False""",
            )
        )

    def handle(self, *args, **options):
        """
        Open the file requested by the user, process any passed options, and
        send the data to the utility functions for processing.
        """
        # Get the file name and read any options
        try:
            file_name = args[0]
        except IndexError:
            raise CommandError("You need to provide the file name")
        categories = LocationCategory.objects.all()
        if len(categories) == 0:
            raise CommandError("""
                You must first create some location
                categories""")
        duplicates_field = options.get('duplicates_field')
        has_header = options.get('has_header')

        # Presuming we do not set the category with a command line option,
        # interrogate the user for which category should be assigned to each
        # new location
        category_choice = -1
        while category_choice not in range(len(categories)):
            self.stdout.write("Please pick an initial location category\r\n\r\n",)
            for (counter, category) in enumerate(categories):
                self.stdout.write("(%s) %s\r\n" % (counter, category))
            self.stdout.write("\r\n\r\n")
            category_choice = raw_input("Category choice: ")
            try:
                category_choice = int(category_choice)
            except ValueError:
                self.stdout.write("\r\nThat wasn't a valid choice!\r\n\r\n")
            else:
                try:
                    assert category_choice in range(len(categories))
                except AssertionError:
                    self.stdout.write("That wasn't a valid choice!\r\n")
        category = categories[category_choice]

        # Open the damn file!
        try:
            csv_file = open(file_name, 'rb')
        except IOError:
            raise CommandError(
                    "There was a problem reading the file, %s" % file_name)
        results = locations_from_csv(csv_file, category, has_header=has_header,
                duplicates_field=duplicates_field)
        self.stdout.write("----------------------------\r\n")
        if results['errors']:
            self.stdout.write("There were errors!\r\n")
            for warning in results['warnings']:
                self.stdout.write("%s\r\n" % warning)
            self.stdout.write("\r\n")
        else:
            self.stdout.write("No errors reported\r\n")
            self.stdout.write("%s locations created\r\n" % len(results['created']))
            self.stdout.write("%s duplicates skipped\r\n" % len(results['skipped']))
        self.stdout.write("----------------------------\r\n")
