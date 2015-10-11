.. _document:

========
Document
========

.. module:: jsl.document

.. autodata:: ALL_OF

.. autodata:: INLINE

.. autoclass:: Options
    :members:

.. autoclass:: Document
    :members: get_schema, get_definitions_and_schema, is_recursive, get_definition_id,
              resolve_field, iter_fields, resolve_and_iter_fields, walk, resolve_and_walk

.. autoclass:: DocumentMeta
    :members: options_container, collect_fields, collect_options, create_options
