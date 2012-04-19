from django.contrib.admin.filterspecs import FilterSpec
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _


class NullableFieldFilterSpec(FilterSpec):
    """
    Basically a slightly modified version of the BooleanFieldFilterSpec
    """
    def __init__(self, f, request, params, model, model_admin,
                 field_path=None):
        super(NullableFieldFilterSpec, self).__init__(f, request, params, model,
                                                     model_admin,
                                                     field_path=field_path)
        self.lookup_kwarg = '%s__isnull' % self.field_path
        self.lookup_kwarg2 = '%s__isnull' % self.field_path
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)
        self.lookup_val2 = request.GET.get(self.lookup_kwarg2, None)

    def title(self):
        return "has geocoding"

    def choices(self, cl):
        for k, v in ((_('All'), None), (_('Yes'), 'False'), (_('No'), 'True')):
            yield {'selected': self.lookup_val == v and not self.lookup_val2,
                   'query_string': cl.get_query_string(
                                   {self.lookup_kwarg: v},
                                   [self.lookup_kwarg2]),
                   'display': k}


class StateFieldFilterSpec(FilterSpec):
    def __init__(self, f, request, params, model, model_admin,
                 field_path=None):
        super(StateFieldFilterSpec, self).__init__(f, request, params, model,
                                            model_admin, field_path=field_path)
        self.lookup_kwarg = '%s__exact' % self.field_path
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)

    def title(self):
        return "state"

    def choices(self, cl):
        from .models import Location
        state_choices = set([(loc.state, loc.get_state_display()) for
            loc in Location.objects.all()])
        state_choices = sorted(list(state_choices), key=lambda ch: ch[0])
        yield {
            'selected': self.lookup_val is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display': _('All')
        }
        #for lookup, title in self.field.flatchoices:
        for lookup, title in state_choices:
            yield {
                'selected': smart_unicode(lookup) == self.lookup_val,
                'query_string': cl.get_query_string({
                                    self.lookup_kwarg: lookup}),
                'display': title,
            }



FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'got_geocoding',
    False), NullableFieldFilterSpec))
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'filter_state',
    False), StateFieldFilterSpec))

