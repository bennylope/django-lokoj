# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Location.state'
        db.alter_column('locations_location', 'state', self.gf('django.contrib.localflavor.us.models.USStateField')(max_length=2))

        # Changing field 'Location.postal_code'
        db.alter_column('locations_location', 'postal_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True))

        # Changing field 'Location.street_address'
        db.alter_column('locations_location', 'street_address', self.gf('django.db.models.fields.CharField')(max_length=200, null=True))


    def backwards(self, orm):
        
        # Changing field 'Location.state'
        db.alter_column('locations_location', 'state', self.gf('django.db.models.fields.CharField')(max_length=2))

        # User chose to not deal with backwards NULL issues for 'Location.postal_code'
        raise RuntimeError("Cannot reverse this migration. 'Location.postal_code' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Location.street_address'
        raise RuntimeError("Cannot reverse this migration. 'Location.street_address' and its values cannot be restored.")


    models = {
        'locations.location': {
            'Meta': {'ordering': "['name']", 'object_name': 'Location'},
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['locations.LocationCategory']", 'symmetrical': 'False'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '15', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '15', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'max_length': '2'}),
            'street_address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'upload_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'locations.locationcategory': {
            'Meta': {'object_name': 'LocationCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'})
        }
    }

    complete_apps = ['locations']
