# coding: utf-8
from __future__ import unicode_literals

import mock
import pytest
import jsonschema

from jsl import fields
from jsl.document import Document


def check_field_schema(field):
    return jsonschema.Draft4Validator.check_schema(field.get_schema())


def test_base_schema_field():
    f = fields.BaseSchemaField()
    assert not f.required
    assert not f.default
    assert not f.enum

    f = fields.BaseSchemaField(required=True)
    assert f.required

    f = fields.BaseSchemaField(default=123)
    assert f.default == 123

    f = fields.BaseSchemaField(default=lambda: 123)
    assert f.default == 123

    f = fields.BaseSchemaField(title='Title', description='Description',
                               enum=lambda: [1, 2, 3], default=lambda: 123)
    assert f.title == 'Title'

    assert f._get_common_schema_fields() == {
        'title': 'Title',
        'description': 'Description',
        'enum': [1, 2, 3],
        'default': 123,
    }


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
    check_field_schema(f)

    with pytest.raises(ValueError) as e:
        fields.StringField(pattern='(')
    assert str(e.value) == 'Invalid regular expression: unbalanced parenthesis'


def test_string_derived_fields():
    f = fields.EmailField()
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'string',
        'format': 'email',
    })
    check_field_schema(f)

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
    check_field_schema(f)

    f = fields.NumberField(minimum=0, maximum=10, exclusive_minimum=True)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'number',
        'exclusiveMinumum': True,
        'minimum': 0,
        'maximum': 10,
    })
    check_field_schema(f)

    f = fields.NumberField(enum=(1, 2, 3))
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'number',
        'enum': [1, 2, 3],
    })
    check_field_schema(f)

    f = fields.IntField()
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'integer',
    })
    check_field_schema(f)


def test_array_field():
    items_mock = fields.StringField()

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

    additional_items_mock = fields.DictField()
    f = fields.ArrayField(items_mock, additional_items=additional_items_mock)
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'array',
        'items': items_mock.get_schema(),
        'additionalItems': additional_items_mock.get_schema(),
    })

    item_1_mock = fields.NumberField()
    item_2_mock = fields.ArrayField(fields.StringField())
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
    check_field_schema(f)

    a_field_mock = fields.StringField()
    b_field_mock = fields.BooleanField()
    c_field_mock = fields.EmailField()
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

    additional_prop_field_mock = fields.OneOfField((fields.StringField(), fields.NumberField()))
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

    # test nested required fields
    f = fields.DictField(properties={
        'a': fields.StringField(required=True),
    }, pattern_properties={
        'c*': fields.StringField(required=True),
    })
    assert f.get_definitions_and_schema() == ({}, {
        'type': 'object',
        'properties': {
            'a': {'type': 'string'},
        },
        'patternProperties': {
            'c*': {'type': 'string'},
        },
        'required': ['a'],
    })
    check_field_schema(f)

    # TODO test DictField.walk


def test_document_field():
    document_cls_mock = mock.Mock()
    expected_schema = mock.Mock()
    attrs = {
        'get_definitions_and_schema.return_value': ({}, expected_schema),
        '_get_definition_id.return_value': 'document.Document',
    }
    document_cls_mock.configure_mock(**attrs)

    f = fields.DocumentField(document_cls_mock)
    definitions, schema = f.get_definitions_and_schema()
    assert not definitions
    assert schema == expected_schema

    definitions, schema = f.get_definitions_and_schema(ref_documents=set([document_cls_mock]))
    assert not definitions
    assert schema == {'$ref': '#/definitions/document.Document'}

    f = fields.DocumentField(document_cls_mock, as_ref=True)
    definitions, schema = f.get_definitions_and_schema()
    assert definitions == {'document.Document': expected_schema}
    assert schema == {'$ref': '#/definitions/document.Document'}



def test_recursive_document_field():
    class Tree(Document):
        node = fields.OneOfField([
            fields.ArrayField(fields.DocumentField('self')),
            fields.StringField(),
        ])

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
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
                                'type': 'string',
                            },
                        ],
                    },
                },
            },
        },
        '$ref': '#/definitions/test_fields.Tree',
    }
    assert Tree.get_schema() == expected_schema
    check_field_schema(Tree)


def test_of_fields():
    field_1_mock = fields.StringField()
    field_2_mock = fields.BooleanField()
    field_3_mock = fields.ArrayField(fields.IntField())
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
