.. _exceptions:

==========
Exceptions
==========

.. module:: jsl.exceptions

.. autoclass:: SchemaGenerationException
    :members:

Steps
-----

Steps attached to a :class:`~.SchemaGenerationException` serve as a traceback
and help a user to debug the error in the document or field description.

.. autoclass:: Step
    :members:
.. autoclass:: DocumentStep
    :show-inheritance:
.. autoclass:: FieldStep
    :show-inheritance:
.. autoclass:: AttributeStep
    :show-inheritance:
.. autoclass:: ItemStep
    :show-inheritance:
