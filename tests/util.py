# coding: utf-8
import collections

import jsonschema

from jsl._compat import iteritems, string_types


def sort_required_keys(schema):
    for key, value in iteritems(schema):
        if (key == 'required' and
                isinstance(value, list) and
                all(isinstance(v, string_types) for v in value)):
            value.sort()
        elif isinstance(value, dict):
            sort_required_keys(value)
        elif isinstance(value, collections.Iterable):
            for v in value:
                if isinstance(v, dict):
                    sort_required_keys(v)


def s(schema):
    jsonschema.Draft4Validator.check_schema(schema)
    sort_required_keys(schema)
    return schema
