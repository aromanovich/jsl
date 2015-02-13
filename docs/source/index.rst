JSL
===

Release v\ |version|.

Introduction
------------

JSL is a Python DSL for describing JSON schemas.

JSL stands for JSON Schema Language.

Examples
--------

    >>> infer('''
    ... {% for row in items|batch(3, '&nbsp;') %}
    ...     {% for column in row %}
    ...         {% if column.has_title %}
    ...             {{ column.title }}
    ...         {% else %}
    ...             {{ column.desc|truncate(10) }}
    ...         {% endif %}
    ...     {% endfor %}
    ... {% endfor %}
    ... ''')
    {
        'items': [{
            'desc': <scalar>,
            'has_title': <unknown>,
            'title': <scalar>
        }]
    }

.. links

.. _opening a ticket: https://github.com/aromanovich/jinja2schema/issues
.. _Jinja2: http://jinja.pocoo.org/docs/
.. _Alpaca: http://www.alpacajs.org/
.. _angular-schema-form: https://github.com/Textalk/angular-schema-form
.. _JSON Editor: https://github.com/jdorn/json-editor
.. _JSON schema: http://json-schema.org/

How It Works
------------


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
