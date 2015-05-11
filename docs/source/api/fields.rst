.. _fields:

======
Fields
======

.. module:: jsl.fields

Primitive Fields
================

.. autoclass:: NullField
    :members:

.. autoclass:: BooleanField
    :members:

.. autoclass:: NumberField
    :members:

.. autoclass:: IntField
    :members:
    :show-inheritance:
.. autoclass:: StringField
    :members:

.. autoclass:: EmailField
    :members:
    :show-inheritance:

.. autoclass:: IPv4Field
    :members:
    :show-inheritance:

.. autoclass:: DateTimeField
    :members:
    :show-inheritance:

.. autoclass:: UriField
    :members:
    :show-inheritance:

Compound Fields
===============

.. data:: RECURSIVE_REFERENCE_CONSTANT

    A special value to be used as an argument to create
    a recursive :class:`.DocumentField`.

.. autoclass:: DocumentField
    :members:

.. autoclass:: ArrayField
    :members:

.. autoclass:: DictField
    :members:

.. autoclass:: NotField
    :members:

.. autoclass:: OneOfField
    :members:

.. autoclass:: AnyOfField
    :members:

.. autoclass:: AllOfField
    :members:

Base Classes
============

.. autoclass:: BaseField
   :members:

.. autoclass:: BaseSchemaField
    :members:
