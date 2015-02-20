# coding: utf-8
#
# This code mostly is a copy-paste from Monk (https://pypi.python.org/pypi/monk) library.
#

class DotExpandedDictMixin(object):
    """Makes the dictionary dot-expandable by exposing dictionary members
    via ``__getattr__`` and ``__setattr__`` in addition to ``__getitem__`` and
    ``__setitem__``. For example, this is the default API::

        data = {'foo': {'bar': 0 } }
        print data['foo']['bar']
        data['foo']['bar'] = 123

    This mixin adds the following API::

        print data.foo.bar
        data.foo.bar = 123

    Nested dictionaries are converted to dot-expanded ones on adding.
    """
    def _make_dot_expanded(self):
        for key, value in self.items():
            self[key] = make_dot_expanded(value)

    def __getattr__(self, attr):
        if not attr.startswith('_') and attr in self:
            return self[attr]
        raise AttributeError('Attribute or key {0.__class__.__name__}.{1} '
                             'does not exist'.format(self, attr))

    def __setattr__(self, attr, value):
        if not attr.startswith('_') and attr in self:
            self[attr] = value
        else:
            # ambigous intent: cannot tell whether user wants to create
            # a dictionary key or actually set an object attribute
            # assuming the first option
            super(DotExpandedDictMixin, self).__setitem__(attr, value)

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, DotExpandedDict):
            value = make_dot_expanded(value)
        super(DotExpandedDictMixin, self).__setitem__(key, value)


class DotExpandedDict(DotExpandedDictMixin, dict):
    def __init__(self, *args, **kwargs):
        super(DotExpandedDict, self).__init__(*args, **kwargs)
        self._make_dot_expanded()


def make_dot_expanded(data):
    if isinstance(data, DotExpandedDictMixin):
        return data
    elif isinstance(data, dict):
        pairs = []
        for key, value in data.items():
            pairs.append((key, make_dot_expanded(value)))
        return DotExpandedDict(pairs)
    elif isinstance(data, list):
        return [make_dot_expanded(x) for x in data]
    return data


class Placeholder(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, objtype):
        if not obj:
            raise AttributeError("type object '{0}' has no attribute '{1}'".format(
                objtype.__name__, self.name))
        return obj.__getattr__(self.name)