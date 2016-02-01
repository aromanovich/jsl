=====================
Overview and Tutorial
=====================

Welcome to JSL!

This document is a brief tour of JSL's features and a quick guide to its
use. Additional documentation can be found in the :ref:`API documentation <api-docs>`.

Introduction
------------

`JSON Schema`_ is a JSON-based format to define the structure of JSON data
for validation and documentation.

JSL is a Python library that provides a DSL for describing JSON schemas.

Why invent a DSL?

* A JSON schema in terms of the Python language is a dictionary. A JSON schema
  of a more or less complex data structure is a dictionary which most likely
  contains a lot of nested dictionaries of dictionaries of dictionaries.
  Writing and maintaining the readability of such a dictionary are not very
  rewarding tasks. They require typing a lot of quotes, braces, colons and commas
  and carefully indenting everything.

* The JSON schema standard is not always intuitive. It takes a little bit of practice
  to remember where to use the ``maxItems`` keyword and where the ``maxLength``,
  or not to forget to set ``additionalProperties`` to false, and so on.

* The syntax is not very concise. The signal-to-noise ratio increases rapidly
  with the complexity of the schema, which makes large schemas difficult to read.

JSL is created to address these issues.
It allows you to define JSON schemas as if they were ORM models --
using classes and fields and relying on the deep metaclass magic under the hood.

Such an approach makes writing and reading schemas easier.
It encourages the decomposition of large schemas into smaller readable pieces
and makes schemas extendable using class inheritance. It enables the autocomplete
feature or IDEs and makes any mistype in a JSON schema keyword cause a RuntimeError.

.. links

.. _Python implementation: https://python-jsonschema.readthedocs.org/en/latest/
.. _JSON Schema: http://json-schema.org/

Quick Example
-------------

::

    import jsl

    class Entry(jsl.Document):
        name = jsl.StringField(required=True)

    class File(Entry):
        content = jsl.StringField(required=True)

    class Directory(Entry):
        content = jsl.ArrayField(jsl.OneOfField([
            jsl.DocumentField(File, as_ref=True),
            jsl.DocumentField(jsl.RECURSIVE_REFERENCE_CONSTANT)
        ]), required=True)

``Directory.get_schema(ordered=True)`` returns the following schema:

::

    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "directory": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "content": {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {"$ref": "#/definitions/file"},
                                {"$ref": "#/definitions/directory"}
                            ]
                        }
                    }
                },
                "required": ["name", "content"],
                "additionalProperties": false
            },
            "file": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["name", "content"],
                "additionalProperties": false
            }
        },
        "$ref": "#/definitions/directory"
    }

Main Features
-------------

JSL introduces the notion of a :ref:`document <document>` and provides a set of :ref:`fields <fields>`.

The schema of a document is always ``{"type": "object"}``, whose ``properties`` contain the
schemas of the fields of the document. A document may be thought of as a :class:`.DictField`
with some special abilities. A document is a class, thus it has a name, by which it can be
referenced from another document and either inlined or included using the
``{"$ref": "..."}`` syntax (see :class:`.DocumentField` and its ``as_ref`` parameter).
Also documents can be recursive.

The most useful method of :class:`.Document` and the fields is :meth:`.Document.get_schema`.

Fields and their parameters are named correspondingly to the keywords described in the
JSON Schema standard. So getting started with JSL will be easy for those familiar with
`the standard`_.

.. _the standard: https://tools.ietf.org/html/draft-zyp-json-schema-04

Variables and Scopes
--------------------

Suppose there is an application that provides a JSON RESTful API backed by MongoDB.
Let's describe a ``User`` data model::

    class User(jsl.Document):
        id = jsl.StringField(required=True)
        login = jsl.StringField(required=True, min_length=3, max_length=20)

``User.get_schema(ordered=True)`` produces the following schema::

    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "additionalProperties": false,
        "properties": {
            "id": {"type": "string"},
            "login": {
                "type": "string",
                "minLength": 3,
                "maxLength": 20
            }
        },
        "required": ["id", "login"]
    }

It describes a response of the imaginary ``/users/<login>/`` endpoint and
perhaps a database document structure (if the application stores users "as is").

Let's now describe a structure of the data required to create a new user
(i.e., a JSON-payload of ``POST``-requests to the imaginary ``/users/`` endpoint).
The data may and may not contain ``id``; if ``id`` is not present, it will
be generated by the application::

    class UserCreationRequest(jsl.Document):
        id = jsl.StringField()
        login = jsl.StringField(required=True, min_length=3, max_length=20)

The only difference between ``User`` and ``UserCreationRequest`` is whether
the ``"id"`` field is required or not.

JSL provides means not to repeat ourselves.

Using Variables
+++++++++++++++

:class:`Variables <.Var>`. are objects which value depends on a given role.
Which value must be used for which role is determined by a list of rules.
A rule is a pair of a matcher and a value. A matcher is a callable that returns
``True`` or ``False`` (or a string or an iterable that will be converted to a lambda).
Here's what it may look like::

    >>> var = jsl.Var([
    ...     # the same as (lambda r: r == 'role_1', 'A')
    ...     ('role_1', 'A'),
    ...     # the same as (lambda r: r in ('role_2', 'role_3'), 'A')
    ...     (('role_2', 'role_3'), 'B'),
    ...     (lambda r: r.startswith('bad_role_'), 'C'),
    ... ], default='D')
    >>> var.resolve('role_1')
    Resolution(value='A', role='role_1')
    >>> var.resolve('role_2')
    Resolution(value='B', role='role_2')
    >>> var.resolve('bad_role_1')
    Resolution(value='C', role='bad_role_1')
    >>> var.resolve('qwerty')
    Resolution(value='D', role='qwerty')

Variables can be used instead of regular values almost everywhere in JSL --
e.g., they can be added to documents, passed as arguments to :class:`fields <.BaseField>`
or even used as properties of a :class:`.DictField`.

Let's introduce a couple of **roles** for our ``User`` document::

    # to describe structures of POST requests
    REQUEST_ROLE = 'request'
    # to describe structures of responses
    RESPONSE_ROLE = 'response'
    # to describe structures of database documents
    DB_ROLE = 'db'

Create a variable ``true_if_not_requests`` which is only ``True`` when the role is
``REQUEST_ROLE``::

    true_if_not_request = jsl.Var({
        jsl.not_(REQUEST_ROLE): True
    })

And describe ``User`` and ``UserCreationRequest`` in a single document
using ``true_if_not_requests`` for the ``required`` argument of the ``id`` field::

    class User(jsl.Document):
        id = jsl.StringField(required=true_if_not_request)
        login = jsl.StringField(required=True, min_length=3, max_length=20)

The ``role`` argument can be specified for the :meth:`.Document.get_schema` method::

    User.get_schema(ordered=True, role=REQUEST_ROLE)

That call will return the following schema. Note that ``"id"`` is not listed as required::

    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "additionalProperties": false,
        "properties": {
            "id": {"type": "string"},
            "login": {
                "type": "string",
                "minLength": 3,
                "maxLength": 20
            }
        },
        "required": ["login"]
    }


Using Scopes
++++++++++++

Let's add a ``version`` field to the ``User`` document with the following
requirements in mind: it is stored in the database, but must not appear
neither in the request nor the response (a reason for this can be that HTTP
headers such as ``ETag`` and ``If-Match`` are used for concurrency control).

One way is to turn the ``version`` field into a variable that only resolves
to the field when the current role is ``DB_ROLE`` and resolves to
``None`` otherwise::

    class User(jsl.Document):
        id = jsl.StringField(required=true_if_not_request)
        login = jsl.StringField(required=True, min_length=3, max_length=20)
        version = jsl.Var({
            DB_ROLE: jsl.StringField(required=True)
        })

Another (and more preferable) way is to use :class:`scopes <.Scope>`::

    class User(jsl.Document):
        id = jsl.StringField(required=true_if_not_request)
        login = jsl.StringField(required=True, min_length=3, max_length=20)

        with jsl.Scope(DB_ROLE) as db_scope:
            db_scope.version = jsl.StringField(required=True)

A scope is a set of :class:`fields <.BaseField>` and a matcher.
A scope can be added to a document, and if the matcher of a scope returns ``True``,
its fields will be present in the resulting schema.

A document may contain arbitrary number of scopes::

    class Message(jsl.Document):
        created_at = jsl.IntField(required=True)
        content = jsl.StringField(required=True)

    class User(jsl.Document):
        id = jsl.StringField(required=true_if_not_request)
        login = jsl.StringField(required=True, min_length=3, max_length=20)

        with jsl.Scope(jsl.not_(REQUEST_ROLE)) as full_scope:
            # a new user can not have messages
            full_scope.messages = jsl.ArrayField(
                jsl.DocumentField(Message), required=True)

        with jsl.Scope(DB_ROLE) as db_scope:
            db_scope.version = jsl.StringField(required=True)

Now ``User.get_schema(ordered=True, role=DB_ROLE)`` returns the following schema::

    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "additionalProperties": false,
        "properties": {
            "id": {"type": "string"},
            "login": {
                "type": "string",
                "minLength": 3,
                "maxLength": 20
            },
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                        "created_at": {
                            "type": "integer"
                        },
                        "content": {
                            "type": "string"
                        }
                    },
                    "required": ["created_at", "content"]
                }
            },
            "version": {"type": "string"}
        },
        "required": ["id", "login", "messages", "version"]
    }

.. _inheritance:

Document Inheritance
--------------------
There are two inheritance modes available in JSL: **inline** and **all-of**.

In the inline mode (used by default), a schema of the child document contains a copy
of its parent's fields.

In the all-of mode a schema of the child document is an allOf validator that contains references
to all parent schemas along with the schema that defines the child's fields.

The inheritance mode can be set using the ``inheritance_mode`` document :class:`option <.Options>`.

Example
+++++++

Suppose we have a `Shape` document::

    class Shape(Base):
        class Options(object):
            definition_id = 'shape'

        color = StringField()

The table below shows the difference between inline and all-of modes:

.. list-table::
    :widths: 50 50
    :header-rows: 1

    * - Inline
      - All-of
    * - ::

            class Circle(Shape):
                class Options(object):
                    definition_id = 'circle'
                    # inheritance_mode = INLINE

                radius = NumberField()

      - ::

            class Circle(Shape):
                class Options(object):
                    definition_id = 'circle'
                    inheritance_mode = ALL_OF

                radius = NumberField()
    * - Resulting schema::

            {
                "type": "object",
                "properties": {
                    "color": {
                        "type": "string"
                    },
                    "radius": {
                        "type": "number"
                    }
                }
            }

      - Resulting schema::

            {
                "definitions": {
                    "shape": {
                        "type": "object",
                        "properties": {
                            "color": {
                                "type": "string"
                            }
                        }
                    }
                },
                "allOf": [
                    {
                        "$ref": "#/definitions/shape"
                    },
                    {
                        "type": "object",
                        "properties": {
                            "radius": {
                                "type": "number"
                            }
                        }
                    }
                ]
            }

More Examples
-------------

A `JSON schema from the official documentation`_ defined using JSL:

::

    class DiskDevice(jsl.Document):
        type = jsl.StringField(enum=['disk'], required=True)
        device = jsl.StringField(pattern='^/dev/[^/]+(/[^/]+)*$', required=True)

    class DiskUUID(jsl.Document):
        type = jsl.StringField(enum=['disk'], required=True)
        label = jsl.StringField(pattern='^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-'
                                        '[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$',
                                required=True)

    class NFS(jsl.Document):
        type = jsl.StringField(enum=['nfs'], required=True)
        remotePath = jsl.StringField(pattern='^(/[^/]+)+$', required=True)
        server = jsl.OneOfField([
            jsl.StringField(format='ipv4'),
            jsl.StringField(format='ipv6'),
            jsl.StringField(format='host-name'),
        ], required=True)

    class TmpFS(jsl.Document):
        type = jsl.StringField(enum=['tmpfs'], required=True)
        sizeInMb = jsl.IntField(minimum=16, maximum=512, required=True)

    class FSTabEntry(jsl.Document):
        class Options(object):
            description = 'schema for an fstab entry'

        storage = jsl.OneOfField([
            jsl.DocumentField(DiskDevice, as_ref=True),
            jsl.DocumentField(DiskUUID, as_ref=True),
            jsl.DocumentField(NFS, as_ref=True),
            jsl.DocumentField(TmpFS, as_ref=True),
        ], required=True)
        fstype = jsl.StringField(enum=['ext3', 'ext4', 'btrfs'])
        options = jsl.ArrayField(jsl.StringField(), min_items=1, unique_items=True)
        readonly = jsl.BooleanField()

.. _JSON schema from the official documentation: http://json-schema.org/example2.html
