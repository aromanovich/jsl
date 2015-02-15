JSL
===

Release v\ |version|.

Introduction
------------

JSON Schema (and its Python implementation) is a wonderful tool for data validation.

But schemas can be tiresome to write, especially large ones. The standard is not always
intuitive and leaves some places to make a mistake. It is easy to mix ``maxItems`` keyword with ``maxLength``,
or to forget to set ``additionalProperties`` to false, and so on.

The syntax is not very concise and large or recursive schema definitions are not easy to comprehend.

JSL is a Python library that adresses this issues by providing a DSL for describing JSON schemas.
The DSL allows you to define a JSON schema in the way similar to how you define a model using an ORM --
using classes and fields and relying on some metaclass-magic under the hood.

Examples
--------

    # TODO


.. links

.. _Python implementation: https://python-jsonschema.readthedocs.org/en/latest/
.. _JSON Schema: http://json-schema.org/

Installation
------------

.. code-block:: sh

    $ pip install jsl

API
---

.. toctree::

    api

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
