# coding: utf-8
from __future__ import unicode_literals

import mock
import pytest

from jsl import fields
from jsl.document import Document


class FieldMock(mock.MagicMock):
    def get_definitions_and_schema(self, definitions=None):
        return definitions or {}, self.to_schema_asdw813s()

    def get_schema(self):
        return self.to_schema_asdw813s()


def test_base_field():
    f = fields.BaseField()
    assert not f.required
    assert not f.default
    assert not f.enum

    f = fields.BaseField(required=True)
    assert f.required

    f = fields.BaseField(default=123)
    assert f.default == 123

    f = fields.BaseField(default=lambda: 123)
    assert f.default == 123

    f = fields.BaseField(title='Description')
    assert f.title == 'Description'


def test_string_field():
    f = fields.StringField()
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'string',
    })

    f = fields.StringField(min_length=1, max_length=10, pattern='^test$', enum=('a', 'b', 'c'),
                           title='Pururum')
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'string',
        'minLength': 1,
        'maxLength': 10,
        'pattern': '^test$',
        'enum': ['a', 'b', 'c'],
        'title': 'Pururum',
    })

    with pytest.raises(ValueError) as e:
        fields.StringField(pattern='(')
    assert str(e.value) == 'Invalid regular expression: unbalanced parenthesis'


def test_string_derived_fields():
    f = fields.EmailField()
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'string',
        'format': 'email',
    })

    f = fields.IPv4Type()
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'string',
        'format': 'ipv4',
    })

    f = fields.DateTimeField()
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'string',
        'format': 'date-time',
    })

    f = fields.UriField()
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'string',
        'format': 'uri',
    })


def test_number_and_int_fields():
    f = fields.NumberField(multiple_of=10)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'number',
        'multipleOf': 10,
    })

    f = fields.NumberField(minimum=0, maximum=10, exclusive_minimum=True)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'number',
        'exclusiveMinumum': True,
        'minimum': 0,
        'maximum': 10,
    })

    f = fields.NumberField(enum=(1, 2, 3))
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'number',
        'enum': [1, 2, 3],
    })

    f = fields.IntField()
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'integer',
    })


def test_array_field():
    items_mock = FieldMock()

    f = fields.ArrayField(items_mock)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'array',
        'items': items_mock.get_schema(),
    })

    f = fields.ArrayField(items_mock, min_items=0, max_items=10, unique_items=True)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'array',
        'items': items_mock.get_schema(),
        'minItems': 0,
        'maxItems': 10,
        'uniqueItems': True,
    })

    f = fields.ArrayField(items_mock, additional_items=True)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'array',
        'items': items_mock.get_schema(),
        'additionalItems': True,
    })

    additional_items_mock = FieldMock()
    f = fields.ArrayField(items_mock, additional_items=additional_items_mock)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'array',
        'items': items_mock.get_schema(),
        'additionalItems': additional_items_mock.get_schema(),
    })

    item_1_mock = FieldMock()
    item_2_mock = FieldMock()
    f = fields.ArrayField([item_1_mock, item_2_mock])
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'array',
        'items': [item_1_mock.get_schema(), item_2_mock.get_schema()],
    })


def test_dict_field_to_schema():
    f = fields.DictField(title='Hey!', enum=[{'x': 1}, {'y': 2}])
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'object',
        'enum': [
            {'x': 1},
            {'y': 2},
        ],
        'title': 'Hey!',
    })

    a_field_mock = FieldMock()
    b_field_mock = FieldMock()
    c_field_mock = FieldMock()
    f = fields.DictField(properties={
        'a': a_field_mock,
        'b': b_field_mock,
    }, pattern_properties={
        'c*': c_field_mock,
    }, min_properties=5, max_properties=10)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'object',
        'properties': {
            'a': a_field_mock.get_schema(),
            'b': b_field_mock.get_schema(),
        },
        'patternProperties': {
            'c*': c_field_mock.get_schema(),
        },
        'minProperties': 5,
        'maxProperties': 10,
    })

    additional_prop_field_mock = FieldMock()
    f = fields.DictField(additional_properties=additional_prop_field_mock)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'object',
        'additionalProperties': additional_prop_field_mock.get_schema(),
    })
    f = fields.DictField(additional_properties=False)
    assert f.get_schema()['additionalProperties'] is False

    f = fields.DictField(pattern_properties={'(': fields.StringField()})
    with pytest.raises(ValueError) as e:
        f.get_definitions_and_schema()
    assert str(e.value) == 'Invalid regular expression: unbalanced parenthesis'


def test_document_field():
    document_cls_mock = mock.MagicMock()
    f = fields.DocumentField(document_cls_mock)
    assert f.get_definitions_and_schema() == document_cls_mock.get_definitions_and_schema()


def test_recursive_document_field():
    class Tree(Document):
        node = fields.OneOfField([
            fields.ArrayField(fields.DocumentField('self')),
            fields.StringField(),
        ])

    expected_schema = {
        'definitions': {
            'test_fields.Tree': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'node': {
                        'oneOf': [
                            {
                                'type': 'array',
                                'items': {'$ref': '#/definitions/test_fields.Tree'},
                            },
                            {
                                'type': 'string'
                            },
                        ]
                    }
                }
            }
        },
        '$ref': '#/definitions/test_fields.Tree',
    }
    assert Tree.get_schema() == expected_schema


def test_of_fields():
    field_1_mock = FieldMock()
    field_2_mock = FieldMock()
    field_3_mock = FieldMock()
    of_fields = [field_1_mock, field_2_mock, field_3_mock]

    f = fields.OneOfField(of_fields)
    assert f.get_definitions_and_schema() == (
        {}, {
            'oneOf': [f.get_schema() for f in of_fields]
        }
    )

    f = fields.AnyOfField(of_fields)
    assert f.get_definitions_and_schema() == (
        {}, {
            'anyOf': [f.get_schema() for f in of_fields]
        }
    )

    f = fields.AllOfField(of_fields)
    assert f.get_definitions_and_schema() == (
        {}, {
            'allOf': [f.get_schema() for f in of_fields]
        }
    )


def test_not_field():
    f = fields.NotField(fields.StringField(), description='Not a string.')
    expected_schema = {
        'description': 'Not a string.',
        'not': {'type': 'string'},
    }
    assert f.get_schema() == expected_schema
