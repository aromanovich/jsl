# coding: utf-8
from ._compat import OrderedDict, iteritems, string_types


DEFAULT_ROLE = 'default'


def not_(role):
    return lambda r: r != role


def all_():
    return lambda r: True


def all_but(*args):
    return lambda r: (r not in args)


class BaseMatcher(object):
    def match(self, role):
        raise NotImplementedError


class EqualityMatcher(BaseMatcher):
    def __init__(self, role):
        self.role = role

    def match(self, role):
        return self.role == role


class FuncMatcher(BaseMatcher):
    def __init__(self, func):
        self.func = func

    def match(self, role):
        return self.func(role)


def construct_matcher(matcher):
    if isinstance(matcher, BaseMatcher):
        return matcher
    elif isinstance(matcher, string_types):
        return EqualityMatcher(matcher)
    elif callable(matcher):
        return FuncMatcher(matcher)
    else:
        raise ValueError('Unknown matcher type: {!r}. Only :class:`BaseMatcher`, '
                         'strings and callables are supported.'.format(matcher))


class Resolvable(object):
    def resolve(self, role):
        raise NotImplementedError()

    def resolve_2(self, role):
        raise NotImplementedError()


class Var(Resolvable):
    """
    :type values: dict or list of key-value tuples
    """

    def __init__(self, values=None, default=None, terminate=None, propagate=all_()):
        self._values = []
        if values is not None:
            values = iteritems(values) if isinstance(values, dict) else values
            for matcher, value in values:
                matcher = construct_matcher(matcher)
                self._values.append((matcher, value))
        self.default = default
        if all([terminate, propagate]):
            raise ValueError('terminate and proparate can not be specified at the same time.')
        if not any([terminate, propagate]):
            raise ValueError('Either terminate or proparate must be specified.')
        self._terminate = construct_matcher(terminate) if terminate else None
        self._propagate = construct_matcher(propagate) if propagate else None

    @property
    def values(self):
        return self._values

    @property
    def terminate(self):
        return self._terminate

    @property
    def propagate(self):
        return self._propagate

    def resolve(self, role):
        for matcher, value in self._values:
            if matcher.match(role):
                return value
        return self.default

    def resolve_2(self, role):
        if self._propagate:
            if self._propagate.match(role):
                new_role = role
            else:
                new_role = DEFAULT_ROLE
        elif self._terminate:
            if self._terminate.match(role):
                new_role = DEFAULT_ROLE
            else:
                new_role = role
        return self.resolve(role), new_role


class Scope(object):
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
