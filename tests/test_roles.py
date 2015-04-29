# coding: utf-8
import pytest

from jsl import (Document, BaseSchemaField, StringField, ArrayField, DocumentField, IntField,
                 DateTimeField, NumberField, DictField, NotField,
                 AllOfField, AnyOfField, OneOfField)
from jsl.roles import Var, Scope, not_, all_but, Resolution
from jsl._compat import iteritems


def sort_required_keys(schema):
    for key, value in iteritems(schema):
        if key == 'required' and isinstance(value, list):
            value.sort()
        elif isinstance(value, dict):
            sort_required_keys(value)


def test_var():
    value_1 = object()
    value_2 = object()
    value_3 = object()
    var = Var([
        ('role_1', value_1),
        ('role_2', value_2),
        (not_('role_3'), value_3),
    ])
    assert var.resolve('role_1') == Resolution(value_1, 'role_1')
    assert var.resolve('role_2') == Resolution(value_2, 'role_2')
    assert var.resolve('default') == Resolution(value_3, 'default')

    var = Var([
        (not_('role_3'), value_3),
        ('role_1', value_1),
        ('role_2', value_2),
    ])
    assert var.resolve('role_1') == Resolution(value_3, 'role_1')
    assert var.resolve('role_2') == Resolution(value_3, 'role_2')
    assert var.resolve('default') == Resolution(value_3, 'default')
    assert var.resolve('role_3') == Resolution(None, 'role_3')


DB_ROLE = 'db'
REQUEST_ROLE = 'request'
RESPONSE_ROLE = 'response'
PARTIAL_RESPONSE_ROLE = RESPONSE_ROLE + '_partial'


def test_helpers():
    when = lambda *args: Var({
        all_but(*args): False
    }, default=True)

    assert when(RESPONSE_ROLE).resolve(RESPONSE_ROLE).value
    assert not when(RESPONSE_ROLE).resolve(REQUEST_ROLE).value


def test_scopes_basics():
    when_not = lambda *args: Var({
        all_but(*args): True
    }, default=False)

    when = lambda *args: Var({
        all_but(*args): False
    }, default=True)

    class Message(Document):
        with Scope(DB_ROLE) as db:
            db.uuid = StringField(required=True)
        created_at = IntField(required=when_not(PARTIAL_RESPONSE_ROLE, REQUEST_ROLE))
        text = StringField(required=when_not(PARTIAL_RESPONSE_ROLE))

    class User(Document):
        class Options(object):
            roles_to_propagate = all_but(PARTIAL_RESPONSE_ROLE)

        with Scope(DB_ROLE) as db:
            db._id = StringField(required=True)
            db.version = StringField(required=True)
        with Scope(lambda r: r.startswith(RESPONSE_ROLE) or r == REQUEST_ROLE) as response:
            response.id = StringField(required=when_not(PARTIAL_RESPONSE_ROLE))
        with Scope(all_but(REQUEST_ROLE)) as request:
            request.messages = ArrayField(DocumentField(Message), required=when_not(PARTIAL_RESPONSE_ROLE))

    schema = User.get_schema(role=DB_ROLE)
    sort_required_keys(schema)
    expected_required = sorted(['_id', 'version', 'messages'])
    expected_properties = {
        '_id': {'type': 'string'},
        'version': {'type': 'string'},
        'messages': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'created_at': {'type': 'integer'},
                    'text': {'type': 'string'},
                    'uuid': {'type': 'string'}
                },
                'required': sorted(['uuid', 'created_at', 'text']),
            },
        },
    }
    assert schema['required'] == expected_required
    assert schema['properties'] == expected_properties

    schema = User.get_schema(role=REQUEST_ROLE)
    sort_required_keys(schema)
    expected_required = sorted(['id'])
    expected_properties = {
        'id': {'type': 'string'},
    }
    assert schema['required'] == expected_required
    assert schema['properties'] == expected_properties

    schema = User.get_schema(role=RESPONSE_ROLE)
    sort_required_keys(schema)
    expected_required = sorted(['id', 'messages'])
    expected_properties = {
        'id': {'type': 'string'},
        'messages': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'created_at': {'type': 'integer'},
                    'text': {'type': 'string'},
                },
                'required': sorted(['created_at', 'text']),
            },
        },
    }
    assert schema['required'] == expected_required
    assert schema['properties'] == expected_properties

    schema = User.get_schema(role=PARTIAL_RESPONSE_ROLE)
    sort_required_keys(schema)
    expected_properties = {
        'id': {'type': 'string'},
        'messages': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'created_at': {'type': 'integer'},
                    'text': {'type': 'string'},
                },
                'required': sorted(['created_at', 'text']),
            },
        },
    }
    assert 'required' not in schema
    assert schema['properties'] == expected_properties


def test_base_field():
    _ = lambda value: Var({'role_1': value})
    field = BaseSchemaField(default=_(lambda: 1), enum=_(lambda: [1, 2, 3]), title=_('Title'),
                            description=_('Description'))
    schema = {}
    schema = field._update_schema_with_common_fields(schema)
    assert schema == {}

    schema = field._update_schema_with_common_fields(schema, role='role_1')
    assert schema == {
        'title': 'Title',
        'description': 'Description',
        'enum': [1, 2, 3],
        'default': 1,
    }


def test_string_field():
    _ = lambda value: Var({'role_1': value})
    field = StringField(format=_('date-time'), min_length=_(1), max_length=_(2))
    assert field.get_schema() == {
        'type': 'string'
    }
    assert field.get_schema(role='role_1') == {
        'type': 'string',
        'format': 'date-time',
        'minLength': 1,
        'maxLength': 2,
    }

    with pytest.raises(ValueError) as e:
        StringField(pattern=_('('))
    assert str(e.value) == 'Invalid regular expression: unbalanced parenthesis'


def test_array_field():
    s_f = StringField()
    n_f = NumberField()
    field = ArrayField(Var({
        'role_1': s_f,
        'role_2': n_f,
    }))
    schema = field.get_schema(role='role_1')
    assert schema['items'] == s_f.get_schema()

    schema = field.get_schema(role='role_2')
    assert schema['items'] == n_f.get_schema()

    schema = field.get_schema()
    assert 'items' not in schema

    _ = lambda value: Var({'role_1': value})
    field = ArrayField(s_f, min_items=_(1), max_items=_(2), unique_items=_(True), additional_items=_(True))
    assert field.get_schema() == {
        'type': 'array',
        'items': s_f.get_schema(),
    }
    assert field.get_schema(role='role_1') == {
        'type': 'array',
        'items': s_f.get_schema(),
        'minItems': 1,
        'maxItems': 2,
        'uniqueItems': True,
        'additionalItems': True,
    }


def test_dict_field():
    s_f = StringField()
    _ = lambda value: Var({'role_1': value})
    field = DictField(properties=Var(
        {
            'role_1': {'name': Var({'role_1': s_f})},
            'role_2': {'name': Var({'role_2': s_f})},
        },
        propagate='role_1'
    ), pattern_properties=Var(
        {
            'role_1': {'.*': Var({'role_1': s_f})},
            'role_2': {'.*': Var({'role_2': s_f})},
        },
        propagate='role_1'
    ), additional_properties=_(s_f), min_properties=_(1), max_properties=_(2))
    assert field.get_schema() == {
        'type': 'object'
    }
    assert field.get_schema(role='role_1') == {
        'type': 'object',
        'properties': {
            'name': s_f.get_schema(),
        },
        'patternProperties': {
            '.*': s_f.get_schema(),
        },
        'additionalProperties': s_f.get_schema(),
        'minProperties': 1,
        'maxProperties': 2,
    }
    assert field.get_schema(role='role_2') == {
        'type': 'object',
        'properties': {},
        'patternProperties': {},
    }


@pytest.mark.parametrize(('keyword', 'field_cls'),
                         [('oneOf', OneOfField), ('anyOf', AnyOfField), ('allOf', AllOfField)])
def test_keyword_of_fields(keyword, field_cls):
    s_f = StringField()
    n_f = NumberField()
    i_f = IntField()
    field = field_cls([n_f, Var({'role_1': s_f}), Var({'role_2': i_f})])
    assert field.get_schema() == {
        keyword: [n_f.get_schema()]
    }
    assert field.get_schema(role='role_1') == {
        keyword: [n_f.get_schema(), s_f.get_schema()]
    }
    assert field.get_schema(role='role_2') == {
        keyword: [n_f.get_schema(), i_f.get_schema()]
    }

    field = field_cls(Var({
        'role_1': [n_f, Var({'role_1': s_f}), Var({'role_2': i_f})],
        'role_2': [Var({'role_2': i_f})],
    }, propagate='role_1'))
    assert field.get_schema() == {keyword: []}
    assert field.get_schema(role='role_1') == {
        keyword: [n_f.get_schema(), s_f.get_schema()]
    }
    assert field.get_schema(role='role_2') == {keyword: []}


def test_not_field():
    s_f = StringField()
    field = NotField(Var({'role_1': s_f}))
    assert field.get_schema() == {'not': {}}
    assert field.get_schema(role='role_1') == {'not': s_f.get_schema()}


def test_document_field():
    class B(Document):
        name = Var({
            'response': StringField(required=True),
            'request': StringField(),
        })

    class A(Document):
        id = Var({'response': StringField(required=True)})
        b = DocumentField(B)

    field = DocumentField(A)

    assert list(field.resolve_and_walk()) == [field]

    assert (sorted(field.resolve_and_walk(through_document_fields=True), key=id) ==
            sorted([field, A.b], key=id))

    assert (sorted(field.resolve_and_walk(role='response', through_document_fields=True), key=id) ==
            sorted([
                field,
                A.b,
                A.resolve_field('id', 'response').value,
                B.resolve_field('name', 'response').value,
            ], key=id))

    assert sorted(field.resolve_and_walk(through_document_fields=True, role='request'), key=id) == sorted([
        field,
        A.b,
        B.resolve_field('name', 'request').value,
    ], key=id)


def test_basics():
    class User(Document):
        id = Var({
            'response': IntField(required=True)
        })
        login = StringField(required=True)

    class Task(Document):
        class Options(object):
            title = 'Task'
            description = 'A task.'
            definition_id = 'task'

        id = IntField(required=Var({'response': True}))
        name = StringField(required=True, min_length=5)
        type = StringField(required=True, enum=['TYPE_1', 'TYPE_2'])
        created_at = DateTimeField(required=True)
        author = Var({'response': DocumentField(User)})

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'additionalProperties': False,
        'description': 'A task.',
        'properties': {
            'created_at': {'format': 'date-time', 'type': 'string'},
            'id': {'type': 'integer'},
            'name': {'minLength': 5, 'type': 'string'},
            'type': {'enum': ['TYPE_1', 'TYPE_2'], 'type': 'string'}
        },
        'required': ['created_at', 'type', 'name'],
        'title': 'Task',
        'type': 'object'
    }
    schema = Task.get_schema()
    expected_schema['required'].sort()
    schema['required'].sort()
    assert schema == expected_schema

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Task',
        'description': 'A task.',
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'created_at': {'format': 'date-time', 'type': 'string'},
            'id': {'type': 'integer'},
            'name': {'minLength': 5, 'type': 'string'},
            'type': {'enum': ['TYPE_1', 'TYPE_2'], 'type': 'string'},
            'author': {
                'additionalProperties': False,
                'properties': {
                    'id': {'type': 'integer'},
                    'login': {'type': 'string'}
                },
                'required': ['id', 'login'],
                'type': 'object'
            },
        },
        'required': ['created_at', 'type', 'name', 'id'],
    }
    schema = Task.get_schema(role='response')
    expected_schema['required'].sort()
    expected_schema['properties']['author']['required'].sort()
    schema['required'].sort()
    schema['properties']['author']['required'].sort()
    assert schema == expected_schema


def test_document():
    class A(Document):
        a = Var({'role_1': DocumentField('self')})
    assert not A.is_recursive()
    assert A.is_recursive(role='role_1')
