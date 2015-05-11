Changelog
=========

0.0.9: 2014-04-10
~~~~~~~~~~~~~~~~~

- Introduce the ``ordered`` argument for :meth:`~jsl.document.Document.get_schema` that
  adds the ability to create more readable JSON schemas with ordered parameters.

0.0.8: 2014-03-21
~~~~~~~~~~~~~~~~~

- Add the ability to specify an `id`_ for documents and fields.

0.0.7: 2014-03-11
~~~~~~~~~~~~~~~~~

- More subclassing-friendly :class:`~jsl.document.DocumentMeta` which allows to
  override methods for collecting document fields and options and
  choose a container class for storing options;
- Various minor bugfixes.

0.0.5: 2014-03-01
~~~~~~~~~~~~~~~~~

- Python 3 support by Igor Davydenko.

.. _id: http://tools.ietf.org/html/draft-zyp-json-schema-04#section-7.2
