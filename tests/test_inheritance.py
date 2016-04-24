# coding: utf-8
import pytest

from jsl import (
    NumberField, IntField, DocumentField, StringField, BooleanField,
    Document, ALL_OF, INLINE, ANY_OF, ONE_OF, RECURSIVE_REFERENCE_CONSTANT
)
from util import normalize


def test_inheritance_mode_inline():
    class Child(Document):
        child_attr = IntField()

    class Parent(Child):
        class Options(object):
            inheritance_mode = INLINE

        parent_attr = IntField()

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'properties': {
            'child_attr': {'type': 'integer'},
            'parent_attr': {'type': 'integer'}
        },
        'additionalProperties': False,
    }
    actual_schema = Parent.get_schema()
    assert normalize(actual_schema) == normalize(expected_schema)

    class A(Document):
        a = IntField()

    class B(A):
        b = IntField()

    class C(B):
        c = IntField()

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'properties': {
            'a': {'type': 'integer'},
            'b': {'type': 'integer'},
            'c': {'type': 'integer'},
        },
        'additionalProperties': False,
    }
    actual_schema = C.get_schema()
    assert normalize(actual_schema) == normalize(expected_schema)


def test_inheritance_mode_all_of():
    class Child(Document):
        class Options(object):
            definition_id = 'child'

        child_attr = IntField()

    class Parent(Child):
        class Options(object):
            inheritance_mode = ALL_OF

        parent_attr = IntField()

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'allOf': [
            {'$ref': '#/definitions/child'},
            {
                'type': 'object',
                'properties': {
                    'parent_attr': {'type': 'integer'}
                },
                'additionalProperties': False,
            }
        ],
        'definitions': {
            'child': {
                'type': 'object',
                'properties': {
                    'child_attr': {'type': 'integer'}
                },
                'additionalProperties': False,
            }
        }
    }
    actual_schema = Parent.get_schema()
    assert normalize(actual_schema) == normalize(expected_schema)


def test_inheritance_mode_any_of():
    class Child(Document):
        class Options(object):
            definition_id = 'child'

        child_attr = IntField()

    class Parent(Child):
        class Options(object):
            inheritance_mode = ANY_OF

        parent_attr = IntField()

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'anyOf': [
            {'$ref': '#/definitions/child'},
            {
                'type': 'object',
                'properties': {
                    'parent_attr': {'type': 'integer'}
                },
                'additionalProperties': False,
            }
        ],
        'definitions': {
            'child': {
                'type': 'object',
                'properties': {
                    'child_attr': {'type': 'integer'}
                },
                'additionalProperties': False,
            }
        }
    }
    actual_schema = Parent.get_schema()
    assert normalize(actual_schema) == normalize(expected_schema)


def test_inheritance_mode_one_of():
    class Child(Document):
        class Options(object):
            definition_id = 'child'

        child_attr = IntField()

    class Parent(Child):
        class Options(object):
            inheritance_mode = ONE_OF

        parent_attr = IntField()

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'oneOf': [
            {'$ref': '#/definitions/child'},
            {
                'type': 'object',
                'properties': {
                    'parent_attr': {'type': 'integer'}
                },
                'additionalProperties': False,
            }
        ],
        'definitions': {
            'child': {
                'type': 'object',
                'properties': {
                    'child_attr': {'type': 'integer'}
                },
                'additionalProperties': False,
            }
        }
    }
    actual_schema = Parent.get_schema()
    assert normalize(actual_schema) == normalize(expected_schema)


def test_multiple_inheritance():
    class IntChild(Document):
        class Options(object):
            definition_id = 'int_child'

        foo = IntField()
        bar = IntField()

    class StringChild(Document):
        class Options(object):
            definition_id = 'string_child'

        foo = StringField()
        bar = StringField()

    class Parent(IntChild, StringChild):
        class Options(object):
            inheritance_mode = ONE_OF

        foo = BooleanField()
        bar = BooleanField()

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'oneOf': [
            {'$ref': '#/definitions/int_child'},
            {'$ref': '#/definitions/string_child'},
            {
                'type': 'object',
                'properties': {
                    'foo': {'type': 'boolean'},
                    'bar': {'type': 'boolean'}
                },
                'additionalProperties': False,
            }
        ],
        'definitions': {
            'int_child': {
                'type': 'object',
                'properties': {
                    'foo': {'type': 'integer'},
                    'bar': {'type': 'integer'}
                },
                'additionalProperties': False,
            },
            'string_child': {
                'type': 'object',
                'properties': {
                    'foo': {'type': 'string'},
                    'bar': {'type': 'string'}
                },
                'additionalProperties': False,
            }
        }
    }
    actual_schema = Parent.get_schema()
    assert normalize(actual_schema) == normalize(expected_schema)


def test_invalid_inheritance_mode():
    with pytest.raises(ValueError) as e:
        class Error(Document):
            class Options(object):
                inheritance_mode = 'lapapam'
    assert str(e.value) == (
        "Unknown inheritance mode: 'lapapam'. "
        "Must be one of the following: ['all_of', 'any_of', 'inline', 'one_of']"
    )


def test_nested_inheritance_all_of_parent():
    class Base(Document):
        class Options(object):
            inheritance_mode = ALL_OF
            definition_id = 'base'

        created_at = IntField()

    class Shape(Base):
        class Options(object):
            definition_id = 'shape'
            title = 'Shape'

        color = StringField(required=True)

    class Button(Base):
        class Options(object):
            definition_id = 'button'
            title = 'Button'

        on_click = StringField(required=True)

    class Circle(Shape, Button):
        class Options(object):
            definition_id = 'circle'
            title = 'Circle'

        radius = NumberField(required=True)

    class Sector(Circle):
        class Options(object):
            inheritance_mode = INLINE
            definition_id = 'sector'
            title = 'Sector'

        angle = NumberField(required=True)

    class CircularSegment(Sector):
        class Options(object):
            inheritance_mode = ALL_OF
            definition_id = 'circular_segment'
            title = 'Circular Segment'

        h = NumberField(required=True)

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'allOf': [
            {'$ref': '#/definitions/sector'},
            {
                'type': 'object',
                'title': 'Circular Segment',
                'properties': {
                    'h': {'type': 'number'},
                },
                'additionalProperties': False,
                'required': ['h'],
            }
        ],
        'definitions': {
            'base': {
                'type': 'object',
                'properties': {
                    'created_at': {'type': 'integer'},
                },
                'additionalProperties': False,
            },
            'button': {
                'allOf': [
                    {'$ref': '#/definitions/base'},
                    {
                        'type': 'object',
                        'title': 'Button',
                        'properties': {
                            'on_click': {'type': 'string'},
                        },
                        'additionalProperties': False,
                        'required': ['on_click'],
                    },
                ],
            },
            'shape': {
                'allOf': [
                    {'$ref': '#/definitions/base'},
                    {
                        'type': 'object',
                        'title': 'Shape',
                        'properties': {
                            'color': {'type': 'string'},
                        },
                        'additionalProperties': False,
                        'required': ['color'],
                    },
                ],
            },
            'sector': {
                'allOf': [
                    {'$ref': '#/definitions/button'},
                    {'$ref': '#/definitions/shape'},
                    {
                        'type': 'object',
                        'title': 'Sector',
                        'properties': {
                            'radius': {'type': 'number'},
                            'angle': {'type': 'number'},
                        },
                        'additionalProperties': False,
                        'required': ['angle', 'radius'],
                    }
                ],
            }
        },
    }
    schema = CircularSegment.get_schema()
    assert normalize(schema) == normalize(expected_schema)


def test_nested_inheritance_inline_parent():
    class Base(Document):
        class Options(object):
            inheritance_mode = ALL_OF
            definition_id = 'base'
            title = 'Base'

        a = StringField()

    class Child(Base):
        class Options(object):
            definition_id = 'child'
            title = 'Child'

        b = StringField()
        c = DocumentField(RECURSIVE_REFERENCE_CONSTANT)

    expected_schema = {
        'definitions': {
            'base': {
                'type': 'object',
                'title': 'Base',
                'properties': {
                    'a': {'type': 'string'},
                },
                'additionalProperties': False,
            },
            'child': {
                'allOf': [
                    {'$ref': '#/definitions/base'},
                    {
                        'type': 'object',
                        'title': 'Child',
                        'properties': {
                            'c': {'$ref': '#/definitions/child'},
                            'b': {'type': 'string'}
                        },
                        'additionalProperties': False,
                    }
                ]
            }
        },
        '$schema': 'http://json-schema.org/draft-04/schema#',
        '$ref': '#/definitions/child'
    }
    schema = Child.get_schema()
    assert normalize(schema) == normalize(expected_schema)
