# coding: utf-8
import collections

from ._compat import OrderedDict, iteritems, string_types


DEFAULT_ROLE = 'default'


def not_(role):
    return lambda r: r != role


def all_():
    return lambda r: True


def all_but(*args):
    return lambda r: (r not in args)


def construct_matcher(matcher):
    if callable(matcher):
        return matcher
    elif isinstance(matcher, string_types):
        return lambda r: r == matcher
    elif isinstance(matcher, collections.Iterable):
        choices = frozenset(matcher)
        return lambda r: r in choices
    else:
        raise ValueError(
            'Unknown matcher type {} ({!r}). Only callables, '
            'strings and iterables are supported.'.format(type(matcher), matcher)
        )


Resolution = collections.namedtuple('Resolution', ['value', 'role'])


class Resolvable(object):
    def resolve(self, role):
        """
        :param role: a role
        :type role: str
        :rtype: :class:`Resolution`
        """
        raise NotImplementedError()


class Var(Resolvable):
    """
    Represents a set of values and provides a method to pick one based on the passed role.

    :param values:
        A dictionary or a list of key-value pairs, where keys are matchers
        and values are corresponding values.

        Matchers are callables returning True or False, but strings and
        iterables are also accepted and processed as follows:
        * A string ``s`` will be replaced with a lambda ``lambda r: r == s``;
        * An iterable ``i`` will be replaced with a lambda ``lambda r: r in i``.
    :type values: dict or list of pairs

    :param default:
        A value to return if all matchers returned False.

    :param propagate:
        A matcher that specifies which roles to propagate down to possibly nested
        documents and fields.
    :type propagate: callable, string or iterable
    """

    def __init__(self, values=None, default=None, propagate=all_()):
        self._values = []
        if values is not None:
            values = iteritems(values) if isinstance(values, dict) else values
            for matcher, value in values:
                matcher = construct_matcher(matcher)
                self._values.append((matcher, value))
        self.default = default
        self._propagate = construct_matcher(propagate)

    @property
    def values(self):
        return self._values

    @property
    def propagate(self):
        return self._propagate

    def resolve(self, role):
        """
        :param role: a role
        :type role: str
        :returns:
            A value corresponding to the first matcher that returned True
            and a role to be used for visiting nested documents and fields.
            If :attr:`propagate`` returns True on ``role``, ``role`` itself
            is returned, and ``DEFAULT_ROLE`` otherwise.
        :rtype: :class:`Resolution`
        """
        for matcher, matcher_value in self._values:
            if matcher(role):
                value = matcher_value
                break
        else:
            value = self.default
        new_role = role if self._propagate(role) else DEFAULT_ROLE
        return Resolution(value, new_role)


class Scope(object):
    """
    Can be added to a :class:`Document` description. For example::

        class User(Document):
            with Scope('db_role') as db:
                db._id = StringField(required=True)
                db.version = StringField(required=True)

    Fields defined within the scope will be added as variables (:class:`Var`) to
    the class. If the same field is present in more that one scope, resulting
    :class:`Var` will run scope matchers in the order they were added to the class.
    """

    def __init__(self, matcher):
        # names are chosen to avoid clashing with user field names
        super(Scope, self).__setattr__('__fields__', OrderedDict())
        super(Scope, self).__setattr__('__matcher__', matcher)

    def __getattr__(self, key):
        odict = super(Scope, self).__getattribute__('__fields__')
        if key in odict:
            return odict[key]
        return super(Scope, self).__getattribute__(key)

    def __setattr__(self, key, val):
        self.__fields__[key] = val

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
