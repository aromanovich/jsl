# coding: utf-8
import mock
import pytest

from jsl import fields, Null
from jsl.fields.base import NullSentinel
from jsl.document import Document
from jsl._compat import OrderedDict

from util import s


def test_null_sentinel():
    assert not Null
    with pytest.raises(TypeError):
        NullSentinel()


def test_base_schema_field():
    f = fields.BaseSchemaField()
    assert not f.required
    assert not f.get_default()
    assert not f.get_enum()

    assert f._update_schema_with_common_fields({}, id='qwerty') == {
        'id': 'qwerty',
    }

    f = fields.BaseSchemaField(default=fields.Null)
    assert not f.get_default()
    assert f._update_schema_with_common_fields({}, id='qwerty') == {
        'id': 'qwerty',
        'default': None,
    }

    f = fields.BaseSchemaField(required=True)
    assert f.required

    f = fields.BaseSchemaField(default=123)
    assert f.get_default() == 123

    f = fields.BaseSchemaField(default=lambda: 123)
    assert f.get_default() == 123

    f = fields.BaseSchemaField(title='Title', description='Description',
                               enum=lambda: [1, 2, 3], default=lambda: 123)
    assert f.title == 'Title'

    assert f._update_schema_with_common_fields({}, id='qwerty') == {
        'id': 'qwerty',
        'title': 'Title',
        'description': 'Description',
        'enum': [1, 2, 3],
        'default': 123,
    }


def test_string_field():
    f = fields.StringField()
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {'type': 'string'}

    f = fields.StringField(min_length=1, max_length=10, pattern='^test$',
                           enum=('a', 'b', 'c'), title='Pururum')

    expected_items = [
        ('type', 'string'),
        ('title', 'Pururum'),
        ('enum', ['a', 'b', 'c']),
        ('pattern', '^test$'),
        ('minLength', 1),
        ('maxLength', 10),
    ]
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == dict(expected_items)
    definitions, ordered_schema = f.get_definitions_and_schema(ordered=True)
    assert isinstance(ordered_schema, OrderedDict)
    assert s(ordered_schema) == OrderedDict(expected_items)

    with pytest.raises(ValueError) as e:
        fields.StringField(pattern='(')
    assert str(e.value) == 'Invalid regular expression: unbalanced parenthesis'


def test_string_derived_fields():
    f = fields.EmailField()
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'string',
        'format': 'email',
    }

    f = fields.IPv4Field()
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'string',
        'format': 'ipv4',
    }

    f = fields.DateTimeField()
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'string',
        'format': 'date-time',
    }

    f = fields.UriField()
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'string',
        'format': 'uri',
    }


def test_number_and_int_fields():
    f = fields.NumberField(multiple_of=10)
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'number',
        'multipleOf': 10,
    }

    f = fields.NumberField(minimum=0, maximum=10,
                           exclusive_minimum=True, exclusive_maximum=True)
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'number',
        'exclusiveMinimum': True,
        'exclusiveMaximum': True,
        'minimum': 0,
        'maximum': 10,
    }

    f = fields.NumberField(enum=(1, 2, 3))
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'number',
        'enum': [1, 2, 3],
    }

    f = fields.IntField()
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'integer',
    }


def test_array_field_to_schema():
    s_f = fields.StringField()
    d_f = fields.DictField()

    f = fields.ArrayField(s_f)
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'array',
        'items': s_f.get_schema(),
    }

    expected_items = [
        ('type', 'array'),
        ('id', 'test'),
        ('title', 'Array'),
        ('items', s_f.get_schema()),
        ('additionalItems', d_f.get_schema()),
        ('minItems', 0),
        ('maxItems', 10),
        ('uniqueItems', True),
    ]
    f = fields.ArrayField(s_f, id='test', title='Array',
                          min_items=0, max_items=10, unique_items=True,
                          additional_items=d_f)
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == dict(expected_items)
    definitions, ordered_schema = f.get_definitions_and_schema(ordered=True)
    assert isinstance(ordered_schema, OrderedDict)
    assert s(ordered_schema) == OrderedDict(expected_items)

    f = fields.ArrayField(s_f, additional_items=True)
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'array',
        'items': s_f.get_schema(),
        'additionalItems': True,
    }

    f = fields.ArrayField(s_f, additional_items=d_f)
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'array',
        'items': s_f.get_schema(),
        'additionalItems': d_f.get_schema(),
    }

    n_f = fields.NumberField()
    a_f = fields.ArrayField(fields.StringField())
    f = fields.ArrayField([n_f, a_f])
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'array',
        'items': [n_f.get_schema(), a_f.get_schema()],
    }


def test_array_field_walk():
    aa = fields.StringField()
    a = fields.DictField(properties={'aa': aa})
    b = fields.StringField()
    c = fields.StringField()

    array_field = fields.ArrayField((a, b), additional_items=c)
    path = list(array_field.resolve_and_walk())
    expected_path = [array_field, a, aa, b, c]
    assert path == expected_path

    array_field = fields.ArrayField(a, additional_items=False)
    path = list(array_field.resolve_and_walk())
    expected_path = [array_field, a, aa]
    assert path == expected_path


def test_dict_field_to_schema():
    f = fields.DictField(title='Hey!', enum=[{'x': 1}, {'y': 2}])
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'type': 'object',
        'enum': [
            {'x': 1},
            {'y': 2},
        ],
        'title': 'Hey!',
    }

    a_field_mock = fields.StringField()
    b_field_mock = fields.BooleanField()
    c_field_mock = fields.EmailField()
    f = fields.DictField(properties={
        'a': a_field_mock,
        'b': b_field_mock,
    }, pattern_properties={
        'c*': c_field_mock,
    }, min_properties=5, max_properties=10)
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == {
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
    }

    additional_prop_field_mock = fields.OneOfField(
        (fields.StringField(), fields.NumberField()))
    f = fields.DictField(additional_properties=additional_prop_field_mock)
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == s({
        'type': 'object',
        'additionalProperties': additional_prop_field_mock.get_schema(),
    })
    f = fields.DictField(additional_properties=False)
    assert f.get_schema()['additionalProperties'] is False

    # test nested required fields and make sure that field names
    # do not override property names
    f = fields.DictField(properties={
        'a': fields.StringField(name='A', required=True),
    }, pattern_properties={
        'c*': fields.StringField(name='C', required=True),
    })
    definitions, schema = f.get_definitions_and_schema()
    assert s(schema) == s({
        'type': 'object',
        'properties': {
            'a': {'type': 'string'},
        },
        'patternProperties': {
            'c*': {'type': 'string'},
        },
        'required': ['a'],
    })


def test_dict_field_walk():
    aa = fields.StringField()
    a = fields.DictField(properties={'aa': aa})
    bb = fields.StringField()
    b = fields.DictField(properties={'bb': bb})
    cc = fields.StringField()
    c = fields.DictField(properties={'cc': cc})
    dd = fields.StringField()
    d = fields.DictField(properties={'dd': dd})
    dict_field = fields.DictField(
        properties={
            'a': a,
            'b': b,
        },
        pattern_properties={
            'c': c,
        },
        additional_properties=d
    )
    path = list(dict_field.resolve_and_walk())
    expected_path_1 = [dict_field, a, aa, b, bb, c, cc, d, dd]
    expected_path_2 = [dict_field, b, bb, a, aa, c, cc, d, dd]
    assert path == expected_path_1 or path == expected_path_2


def test_document_field():
    document_cls_mock = mock.Mock()
    expected_schema = mock.Mock()
    attrs = {
        'get_definitions_and_schema.return_value': ({}, expected_schema),
        'get_definition_id.return_value': 'document.Document',
    }
    document_cls_mock.configure_mock(**attrs)

    f = fields.DocumentField(document_cls_mock)
    definitions, schema = f.get_definitions_and_schema()
    assert schema == expected_schema

    definitions, schema = f.get_definitions_and_schema(ref_documents=set([document_cls_mock]))
    assert s(schema) == {'$ref': '#/definitions/document.Document'}

    f = fields.DocumentField(document_cls_mock, as_ref=True)
    definitions, schema = f.get_definitions_and_schema()
    assert definitions == {'document.Document': expected_schema}
    assert s(schema) == {'$ref': '#/definitions/document.Document'}


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
    assert s(Tree.get_schema()) == s(expected_schema)


def test_of_fields():
    field_1_mock = fields.StringField()
    field_2_mock = fields.BooleanField()
    field_3_mock = fields.ArrayField(fields.IntField())
    of_fields = [field_1_mock, field_2_mock, field_3_mock]

    f = fields.OneOfField(of_fields)
    _, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'oneOf': [f.get_schema() for f in of_fields]
    }

    f = fields.AnyOfField(of_fields)
    _, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'anyOf': [f.get_schema() for f in of_fields]
    }

    f = fields.AllOfField(of_fields)
    _, schema = f.get_definitions_and_schema()
    assert s(schema) == {
        'allOf': [f.get_schema() for f in of_fields]
    }


def test_not_field():
    f = fields.NotField(fields.StringField(), description='Not a string.')
    expected_schema = {
        'description': 'Not a string.',
        'not': {'type': 'string'},
    }
    assert s(f.get_schema()) == expected_schema


def test_null_field():
    f = fields.NullField()
    assert s(f.get_schema()) == {'type': 'null'}


def test_ref_field():
    pointer = '#/definitions/User'
    f = fields.RefField(pointer=pointer)
    assert f.get_definitions_and_schema() == ({}, {'$ref': pointer})