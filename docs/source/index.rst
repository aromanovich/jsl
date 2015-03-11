JSL
===

Release v\ |version|.

Introduction
------------

`JSON Schema`_ and its `Python implementation`_ are wonderful tools for data validation.

JSL is a Python library that provides a DSL for describing JSON schemas.

Why? Well, JSON schemas, especially large ones, can be tiresome to write. The standard is not always
intuitive and leaves some places to make a mistake --  for instance, it is easy to mix
``maxItems`` keyword with ``maxLength``, or to forget to set ``additionalProperties`` to false, and so on.
The syntax is not very concise and sometimes schema definitions get clumsy and hard to comprehend.

The DSL allows you to define a JSON schema in the way similar to how you define a model using an ORM --
using classes and fields and relying on some metaclass magic under the hood.

It:
    * makes reading and writing schemas easier;
    * makes easier to decompose large schema definitions into smaller readable pieces;
    * makes schemas extendable using the class inheritance;
    * enables the autocomplete feature of your IDE;
    * prevents you from making mistypes in JSON schema keywords (by throwing a RuntimeError);
    * ...

Let's take a look at examples.

.. links

.. _Python implementation: https://python-jsonschema.readthedocs.org/en/latest/
.. _JSON Schema: http://json-schema.org/

Examples
--------

::

    from jsl import Document, StringField, ArrayField, DocumentField, OneOfField

    class Entry(Document):
        name = StringField(required=True)

    class File(Entry):
        content = StringField(required=True)

    class Directory(Entry):
        content = ArrayField(OneOfField([
            DocumentField(File, as_ref=True),
            DocumentField('self')
        ]), required=True)


``Directory.to_schema()`` will return the following schema:

::

    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "module.File": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                    "content",
                    "name"
                ],
                "properties": {
                    "content": {"type": "string"},
                    "name": {"type": "string"}
                }
            },
            "module.Directory": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                    "content",
                    "name"
                ],
                "properties": {
                    "content": {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {"$ref": "#/definitions/module.File"},
                                {"$ref": "#/definitions/module.Directory"}
                            ]
                        }
                    },
                    "name": {"type": "string"}
                }
            }
        },
        "$ref": "#/definitions/module.Directory"
    }

A `JSON schema from the official documentation`_, defined using JSL:

::

    from jsl import Document, BooleanField, StringField, ArrayField, DocumentField, OneOfField, IntField

    class DiskDevice(Document):
        type = StringField(enum=['disk'], required=True)
        device = StringField(pattern='^/dev/[^/]+(/[^/]+)*$', required=True)

    class DiskUUID(Document):
        type = StringField(enum=['disk'], required=True)
        label = StringField(pattern='^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$',
                            required=True)

    class NFS(Document):
        type = StringField(enum=['nfs'], required=True)
        remotePath = StringField(pattern='^(/[^/]+)+$', required=True)
        server = OneOfField([
            StringField(format='ipv4'),
            StringField(format='ipv6'),
            StringField(format='host-name'),
        ], required=True)

    class TmpFS(Document):
        type = StringField(enum=['tmpfs'], required=True)
        sizeInMb = IntField(minimum=16, maximum=512, required=True)

    class Schema(Document):
        class Options(object):
            schema_uri = 'http://json-schema.org/draft-04/schema#'
            description = 'schema for an fstab entry'

        storage = OneOfField([
            DocumentField(DiskDevice, as_ref=True),
            DocumentField(DiskUUID, as_ref=True),
            DocumentField(NFS, as_ref=True),
            DocumentField(TmpFS, as_ref=True),
        ], required=True)
        fstype = StringField(enum=['ext3', 'ext4', 'btrfs'])
        options = ArrayField(StringField(), min_items=1, unique_items=True)
        readonly = BooleanField()

.. _JSON schema from the official documentation: http://json-schema.org/example2.html

Installation
------------

.. code-block:: sh

    $ pip install jsl

API
---

Document
~~~~~~~~

.. autoclass:: jsl.document.Options
    :members:

.. autoclass:: jsl.document.Document
    :members: get_schema

.. autoclass:: jsl.document.DocumentMeta
    :members: options_container, collect_fields, collect_options, create_options

Fields
~~~~~~

Base Fields
+++++++++++

.. autoclass:: jsl.fields.BaseField
   :members: get_schema

.. autoclass:: jsl.fields.BaseSchemaField
    :members:

Schema Fields
+++++++++++++

.. autoclass:: jsl.fields.DocumentField
.. autoclass:: jsl.fields.ArrayField
.. autoclass:: jsl.fields.DictField

.. autoclass:: jsl.fields.NotField
.. autoclass:: jsl.fields.OneOfField
.. autoclass:: jsl.fields.AnyOfField
.. autoclass:: jsl.fields.AllOfField

.. autoclass:: jsl.fields.BooleanField
.. autoclass:: jsl.fields.StringField
.. autoclass:: jsl.fields.EmailField
.. autoclass:: jsl.fields.IPv4Type
.. autoclass:: jsl.fields.DateTimeField
.. autoclass:: jsl.fields.UriField
.. autoclass:: jsl.fields.UriField
.. autoclass:: jsl.fields.NumberField
.. autoclass:: jsl.fields.IntField


Changelog
---------

0.0.7: 2014-03-11
~~~~~~~~~~~~~~~~~

- More subclassing-friendly :class:`~jsl.document.DocumentMeta` which allows to
  override methods for collecting document fields and options and
  choose a container class for storing options;
- Various minor bugfixes.

0.0.5: 2014-03-01
~~~~~~~~~~~~~~~~~

- Python 3 support by Igor Davydenko.

Contributing
------------

The project is hosted on GitHub_.
Please feel free to send a pull request or open an issue.

.. _GitHub: https://github.com/aromanovich/jsl

Running the Tests
~~~~~~~~~~~~~~~~~

.. code-block:: sh

    $ pip install -r ./requirements-dev.txt
    $ ./test.sh
