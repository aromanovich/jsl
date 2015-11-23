Changelog
=========

0.2.1 2015-11-23
~~~~~~~~~~~~~~~~

- Fix a bug when referencing a recursive document using :class:`.DocumentField` with ``as_ref=True``
  produced circular references (issue `#16`_).

0.2.0 2015-11-08
~~~~~~~~~~~~~~~~

- Minor breaking change for the issue `#15`_: :meth:`.Document.resolve_and_iter_fields`
  now iterates only over fields that are attached as attributes
  (fields specified in document ``Options`` as ``pattern_properties`` or
  ``additional_properties`` won't be processed), and yields tuples of (field name, field).

0.1.5: 2015-10-22
~~~~~~~~~~~~~~~~~

- Fix a bug when using RECURSIVE_REFERENCE_CONSTANT under a scope caused
  infinite recursion (issue `#14`_).

0.1.4: 2015-10-11
~~~~~~~~~~~~~~~~~

- Introduce :ref:`inheritance modes <inheritance>`.

0.1.3: 2015-08-12
~~~~~~~~~~~~~~~~~

- Add a ``name`` parameter to :class:`.BaseField` which makes it possible to create documents
  with fields whose names contain symbols that are not allowed in Python variable
  names (such as hyphen);
- Introduce :class:`.RefField`.

0.1.2: 2015-06-12
~~~~~~~~~~~~~~~~~

- Allow specifying a null default value for fields (see :data:`.Null` value) by Nathan Hoad.

0.1.1: 2015-05-29
~~~~~~~~~~~~~~~~~

- Fix :meth:`.Document.resolve_field` method;
- Allow specifying a resolvable as a ``definition_id`` (see :class:`document options <.Options>`).

0.1.0: 2015-05-13
~~~~~~~~~~~~~~~~~

- Introduce :ref:`roles <roles>`, :class:`variables <.Var>` and :class:`scopes <.Scope>`;
- :class:`.NullField` by Igor Davydenko;
- Almost completely rewritten documentation;
- Various minor fixes.

0.0.10: 2015-04-28
~~~~~~~~~~~~~~~~~~

- Fix spelling of ``exclusiveMinimum`` by Keith T. Star.

0.0.9: 2015-04-10
~~~~~~~~~~~~~~~~~

- Introduce the ``ordered`` argument for :meth:`~jsl.document.Document.get_schema` that
  adds the ability to create more readable JSON schemas with ordered parameters.

0.0.8: 2015-03-21
~~~~~~~~~~~~~~~~~

- Add the ability to specify an `id`_ for documents and fields.

0.0.7: 2015-03-11
~~~~~~~~~~~~~~~~~

- More subclassing-friendly :class:`~jsl.document.DocumentMeta` which allows to
  override methods for collecting document fields and options and
  choose a container class for storing options;
- Various minor bugfixes.

0.0.5: 2015-03-01
~~~~~~~~~~~~~~~~~

- Python 3 support by Igor Davydenko.

.. _id: http://tools.ietf.org/html/draft-zyp-json-schema-04#section-7.2
.. _#14: https://github.com/aromanovich/jsl/issues/14
.. _#15: https://github.com/aromanovich/jsl/issues/15
.. _#16: https://github.com/aromanovich/jsl/issues/16
