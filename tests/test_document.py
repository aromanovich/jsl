# coding: utf-8
from __future__ import unicode_literals

import jsonschema

from jsl.document import Document
from jsl.fields import StringField, IntField, DocumentField, DateTimeField, ArrayField, OneOfField


def check_field_schema(field):
    return jsonschema.Draft4Validator.check_schema(field.get_schema())


def test_to_schema():
    class User(Document):
        class Options(object):
            additional_properties = True
            title = 'User'

        id = IntField(required=True)

    class Resource(Document):
        task_id = IntField(required=True)
        user = DocumentField(User, required=True)

    class Task(Document):
        class Options(object):
            title = 'Task'
            description = 'A task.'
            id = 'http://x.y.z/rootschema.json#'

        name = StringField(required=True, min_length=5)
        type = StringField(required=True, enum=['TYPE_1', 'TYPE_2'])
        resources = ArrayField(DocumentField(Resource))
        created_at = DateTimeField(required=True)
        author = DocumentField(User)

    task_schema = Task.get_schema()
    expected_task_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'id': 'http://x.y.z/rootschema.json#',
        'type': 'object',
        'title': 'Task',
        'description': 'A task.',
        'additionalProperties': False,
        'required': ['created_at', 'type', 'name'],
        'properties': {
            'created_at': Task.created_at.get_schema(),
            'type': Task.type.get_schema(),
            'name': Task.name.get_schema(),
            'resources': Task.resources.get_schema(),
            'author': Task.author.get_schema(),
        }
    }
    assert task_schema == expected_task_schema
    assert task_schema['properties']['author']['additionalProperties']
    check_field_schema(Task)


def test_document_options():
    class Parent(Document):
        class Options(object):
            title = 'Parent'
            additional_properties = True

    class Child(Parent):
        class Options(object):
            title = 'Child'

    assert Parent._options.additional_properties
    assert Child._options.title == 'Child'
    assert Child._options.additional_properties


def test_recursive_definitions_1():
    class A(Document):
        id = StringField()
        b = DocumentField('B')

    class B(Document):
        a = DocumentField(A)
        b = DocumentField('B')
        c = DocumentField('C')

    class C(Document):
        a = DocumentField(A)
        d = DocumentField('D')

    class D(Document):
        id = StringField()

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'definitions': {
            'test_document.A': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'id': {'type': 'string'},
                    'b': {'$ref': '#/definitions/test_document.B'},
                },
            },
            'test_document.B': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'a': {'$ref': '#/definitions/test_document.A'},
                    'b': {'$ref': '#/definitions/test_document.B'},
                    'c': {'$ref': '#/definitions/test_document.C'},
                },
            },
            'test_document.C': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'a': {'$ref': '#/definitions/test_document.A'},
                    'd': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'id': {'type': 'string'}
                        },
                    },
                },
            },
        },
        '$ref': '#/definitions/test_document.A',
    }
    assert A.get_schema() == expected_schema
    check_field_schema(A)


def test_recursive_definitions_2():
    class Main(Document):
        a = DocumentField('test_document.A')
        b = DocumentField('B')

    class A(Document):
        name = StringField()
        a = DocumentField('A')

    class B(Document):
        c = DocumentField('C')

    class C(Document):
        name = StringField()
        c = DocumentField('C')

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'definitions': {
            'test_document.A': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'a': {'$ref': '#/definitions/test_document.A'},
                    'name': {'type': 'string'}
                },
            },
            'test_document.C': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'c': {'$ref': '#/definitions/test_document.C'},
                    'name': {'type': 'string'}
                },
            }
        },
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'a': {'$ref': '#/definitions/test_document.A'},
            'b': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'c': {
                        '$ref': '#/definitions/test_document.C'
                    }
                },
            }
        },
    }
    schema = Main.get_schema()
    assert schema == expected_schema
    check_field_schema(Main)


def test_recursive_definitions_3():
    class Main(Document):
        a = DocumentField('A')

    class A(Document):
        name = StringField()
        b = DocumentField('B')

    class B(Document):
        c = DocumentField(Main)

    expected_definitions = {
        'test_document.A': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'b': {'$ref': '#/definitions/test_document.B'},
                'name': {'type': 'string'}
            },
        },
        'test_document.B': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'c': {'$ref': '#/definitions/test_document.Main'},
            },
        },
        'test_document.Main': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'a': {'$ref': '#/definitions/test_document.A'},
            },
        }
    }
    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'definitions': expected_definitions,
        '$ref': '#/definitions/test_document.Main',
    }
    assert Main.get_schema() == expected_schema
    check_field_schema(Main)


    class X(Document):
        name = StringField()

    class Z(Document):
        main_or_x = OneOfField([
            DocumentField(Main),
            DocumentField(X)
        ])

    expected_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'definitions': expected_definitions,
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'main_or_x': {
                'oneOf': [
                    {'$ref': '#/definitions/test_document.Main'},
                    {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {'name': {'type': 'string'}},
                    }
                ]
            }
        },
    }
    assert Z.get_schema() == expected_schema
    check_field_schema(Z)
