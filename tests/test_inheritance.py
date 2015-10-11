# coding: utf-8
import pytest

from jsl import NumberField, IntField, RECURSIVE_REFERENCE_CONSTANT, DocumentField
from jsl.document import Document, ALL_OF, INLINE
from jsl.fields import StringField
from util import s


def test_inheritance_1():
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
                    {'$ref': '#/definitions/shape'},
                    {'$ref': '#/definitions/button'},
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
    assert s(schema) == s(expected_schema)

    with pytest.raises(ValueError) as e:
        class Error(Document):
            class Options(object):
                inheritance_mode = 'lapapam'
    assert str(e.value) == ("Unknown inheritance mode: 'lapapam'. "
                            "Must be one of the following: ['inline', 'all_of']")


def test_inheritance_2():
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
        "definitions": {
            "base": {
                "type": "object",
                "title": "Base",
                "properties": {
                    "a": {
                        "type": "string"
                    }
                },
                "additionalProperties": False,
            },
            "child": {
                "allOf": [
                    {
                        "$ref": "#/definitions/base"
                    },
                    {
                        "type": "object",
                        "title": "Child",
                        "properties": {
                            "c": {
                                "$ref": "#/definitions/child"
                            },
                            "b": {
                                "type": "string"
                            }
                        },
                        "additionalProperties": False,
                    }
                ]
            }
        },
        "$schema": "http://json-schema.org/draft-04/schema#",
        "$ref": "#/definitions/child"
    }
    schema = Child.get_schema()
    assert s(schema) == s(expected_schema)
