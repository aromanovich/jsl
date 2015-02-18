JSL
===

.. image:: https://travis-ci.org/aromanovich/jsl.svg?branch=master
    :target: https://travis-ci.org/aromanovich/jsl
    :alt: Build Status

.. image:: https://coveralls.io/repos/aromanovich/jsl/badge.svg?branch=master
    :target: https://coveralls.io/r/aromanovich/jsl?branch=master
    :alt: Coverage

Documentation_ | GitHub_ |  PyPI_

JSL is a Python DSL for defining JSON Schemas.

Example
-------

.. code-block:: python

    from jsl import Document, StringField, ArrayField, DocumentField, OneOfField

    class Entry(Document):
        name = StringField(required=True)

    class File(Entry):
        content = StringField(required=True)

    class Directory(Entry):
        content = ArrayField(OneOfField([
            DocumentField(File, as_ref=True),
            DocumentField('self')  # recursion
        ]), required=True)


``Directory.to_schema()`` will return the following schema:

.. code-block:: json

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

Installing
----------

::

    pip install jsl

License
-------

`BSD license`_

.. _Documentation: http://jsl.readthedocs.org/
.. _GitHub: https://github.com/aromanovich/jsl
.. _PyPI: https://pypi.python.org/pypi/jsl
.. _BSD license: https://github.com/aromanovich/jsl/blob/master/LICENSE