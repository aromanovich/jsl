# coding: utf-8
from ._compat import itervalues


DEFAULT_ROLE = 'default'


class Var(object):
    def __init__(self, values=None, roles_to_pass_down=(), **kwargs):
        self.values = kwargs if values is None else values
        self.roles_to_pass_down = roles_to_pass_down

    def resolve(self, role):
        return self.values.get(role)


def maybe_resolve_all_roles(value):
    if isinstance(value, Var):
        return itervalues(value.values)
    return [value]


def maybe_resolve(value, role):
    if isinstance(value, Var):
        return value.resolve(role)
    return value


def maybe_resolve_2(value, role):
    if isinstance(value, Var):
        new_role = role if role in value.roles_to_pass_down else DEFAULT_ROLE
        return value.resolve(role), new_role
    return value, role
