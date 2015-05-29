Changelog
=========

0.1.1: 2015-05-29
~~~~~~~~~~~~~~~~~

- Fix :meth:`.Document.resolve_field` method;
- Allow specifying a resolvable as a ``definition_id`` (see :class:`document options <.Options>`).

0.1.0: 2015-05-13
~~~~~~~~~~~~~~~~~

- Introduce :ref:`roles <roles>`, :class:`variables <.Var>` and :class:`scopes <.Scope>`;
- :class:`.NullField` by Igor Davydenko;
- Almost completely rewritted documentation;
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
