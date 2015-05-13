JSL
===

.. image:: https://travis-ci.org/aromanovich/jsl.svg?branch=master
    :target: https://travis-ci.org/aromanovich/jsl
    :alt: Build Status

.. image:: https://coveralls.io/repos/aromanovich/jsl/badge.svg?branch=master
    :target: https://coveralls.io/r/aromanovich/jsl?branch=master
    :alt: Coverage

.. image:: https://readthedocs.org/projects/jsl/badge/?version=latest
    :target: https://readthedocs.org/projects/jsl/
    :alt: Documentation

.. image:: http://img.shields.io/pypi/v/jsl.svg
    :target: https://pypi.python.org/pypi/jsl
    :alt: PyPI Version

.. image:: http://img.shields.io/pypi/dm/jsl.svg
    :target: https://pypi.python.org/pypi/jsl
    :alt: PyPI Downloads

Documentation_ | GitHub_ |  PyPI_

JSL is a Python DSL for defining JSON Schemas.

Example
-------

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

``Directory.get_schema(ordered=True)`` will return the following JSON schema:

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
