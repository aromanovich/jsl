# coding: utf-8
import collections
import contextlib

from .roles import DEFAULT_ROLE
from ._compat import implements_to_string


@contextlib.contextmanager
def processing(step):
    """
    A context manager. If an :class:`SchemaGenerationException` occurs within
    its nested code block, it adds :param:`step` to it and reraises.
    """
    try:
        yield
    except SchemaGenerationException as e:
        e.add_step(step)
        raise


class Step(object):
    """
    Defines a step of the schema generation process that caused an error.

    :param role: A current role.
    :type role: str
    """

    def __init__(self, entity, role=DEFAULT_ROLE):
        self.entity = entity
        self.role = role

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __repr__(self):
        return '{0}({1!r}, role={2})'.format(
            self.__class__.__name__, self.entity, self.role)


@implements_to_string
class DocumentStep(Step):
    """
    :param entity: A document being processed.
    :type entity: subclass of :class:`Document`
    """

    def __str__(self):
        return self.entity.__name__


@implements_to_string
class FieldStep(Step):
    """
    :param entity: A field being processed.
    :type entity: instance of :class:`BaseField`
    """

    def __str__(self):
        return self.entity.__class__.__name__


@implements_to_string
class AttributeStep(Step):
    """
    :param entity:
        The name of a field's attribute being processed
        (e.g., ``properties``, ``additional_properties``, etc.)
    :type entity: str
    """

    def __str__(self):
        return self.entity


@implements_to_string
class ItemStep(Step):
    """
    :param entity:
        An attribute item being processed
        (i.e., ``"firstname"`` if current attribute is ``properties`` or
        ``0`` if current attribute is ``items``).
    :type entity: str or int
    """

    def __str__(self):
        return repr(self.entity)


@implements_to_string
class SchemaGenerationException(Exception):
    def __init__(self, message):
        self.message = message
        self.steps = collections.deque()

    def add_step(self, step):
        self.steps.appendleft(step)

    def format_steps(self):
        if not self.steps:
            return '-'
        parts = []
        steps = iter(self.steps)
        parts.append(str(next(steps)))
        for step in steps:
            if isinstance(step, (DocumentStep, FieldStep)):
                parts.append(' -> {0}'.format(step))
            elif isinstance(step, AttributeStep):
                parts.append('.{0}'.format(step))
            elif isinstance(step, ItemStep):
                parts.append('[{0}]'.format(step))
        return ''.join(parts)

    def __str__(self):
        return u"{0}\nSteps: {1}".rstrip().format(self.message, self.format_steps())
