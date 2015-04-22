# coding: utf-8
from ._compat import itervalues, OrderedDict, iteritems, string_types


DEFAULT_ROLE = 'default'



class BaseVar(object):
    def resolve(self, role):
        raise NotImplementedError()


class Var(BaseVar):
    """
    :type values: dict or list of key-value tuples
    """
    def __init__(self, values=None, roles_to_pass_down=(), **kwargs):
        self.values = kwargs if values is None else values
        self.roles_to_pass_down = roles_to_pass_down

    def resolve(self, role_to_resolve):
        for role, value in iteritems(OrderedDict(self.values)):
            if isinstance(role, Not):
                if role != role_to_resolve:
                    return value
            elif isinstance(role, string_types) and role == role_to_resolve:
                return value
        return None


class Not(str):
    pass


class IfNot(BaseVar):
    def __init__(self, role, value, roles_to_pass_down=()):
        self.role = role
        self.value = value
        self.roles_to_pass_down = roles_to_pass_down

    def resolve(self, role):
        if role == self.role:
            return self.value
        return None


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
