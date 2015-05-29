# coding: utf-8
import inspect

from . import registry
from .exceptions import processing, DocumentStep
from .fields import BaseField, DocumentField, DictField
from .roles import DEFAULT_ROLE, Var, Scope, all_, construct_matcher, Resolvable, Resolution
from .resolutionscope import ResolutionScope
from ._compat import iteritems, iterkeys, with_metaclass, OrderedDict, Prepareable


def _set_owner_to_document_fields(cls):
    for field in cls.walk(through_document_fields=False, visited_documents=set([cls])):
        if isinstance(field, DocumentField):
            field.owner_cls = cls


class Options(object):
    """
    A container for options.

    All the arguments are the same and work exactly as for :class:`.fields.DictField`
    except ``properties`` (since it is automatically populated with the document fields)
    and these:

    :param definition_id:
        A unique string to be used as a key for this document in the "definitions"
        schema section. If not specified, will be generated from module and class names.
    :type definition_id: str or :class:`.Resolvable`
    :param str schema_uri:
        An URI of the JSON Schema meta-schema.
    :param roles_to_propagate:
        A matcher. If it returns ``True`` for a role, it will be passed to nested
        documents.
    :type roles_to_propagate: callable, string or iterable
    """

    def __init__(self, additional_properties=False, pattern_properties=None,
                 min_properties=None, max_properties=None,
                 title=None, description=None,
                 default=None, enum=None,
                 id='', schema_uri='http://json-schema.org/draft-04/schema#',
                 definition_id=None, roles_to_propagate=None):
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties
        self.min_properties = min_properties
        self.max_properties = max_properties
        self.title = title
        self.description = description
        self.default = default
        self.enum = enum
        self.id = id

        self.schema_uri = schema_uri
        self.definition_id = definition_id
        self.roles_to_propagate = construct_matcher(roles_to_propagate or all_)


class DocumentMeta(with_metaclass(Prepareable, type)):
    """
    A metaclass for :class:`~.Document`. It's responsible for collecting
    options, fields and scopes registering the document in the registry, making
    it the owner of nested :class:`document fields <.DocumentField>` s and so on.
    """
    options_container = Options
    """
    A class to be used by :meth:`~.DocumentMeta.create_options`.
    Must be a subclass of :class:`~.Options`.
    """

    @classmethod
    def __prepare__(mcs, name, bases):
        return OrderedDict()

    def __new__(mcs, name, bases, attrs):
        fields = mcs.collect_fields(bases, attrs)
        options_data = mcs.collect_options(bases, attrs)
        options = mcs.create_options(options_data)

        attrs['_fields'] = fields
        attrs['_options'] = options
        attrs['_field'] = DictField(
            properties=fields,
            pattern_properties=options.pattern_properties,
            additional_properties=options.additional_properties,
            min_properties=options.min_properties,
            max_properties=options.max_properties,
            title=options.title,
            description=options.description,
            enum=options.enum,
            default=options.default,
            id=options.id,
        )

        klass = type.__new__(mcs, name, bases, attrs)
        registry.put_document(klass.__name__, klass, module=klass.__module__)
        _set_owner_to_document_fields(klass)
        return klass

    @classmethod
    def collect_fields(mcs, bases, attrs):
        """
        Collects fields from the current class and its parent classes.

        :rtype: a dictionary mapping field names to fields
        """
        fields = OrderedDict()
        # fields from parent classes:
        for base in reversed(bases):
            if hasattr(base, '_fields'):
                fields.update(base._fields)

        to_be_replaced = object()

        # and from the current class:
        pre_fields = OrderedDict()
        scopes = []
        for key, value in iteritems(attrs):
            if isinstance(value, (BaseField, Resolvable)):
                pre_fields[key] = value
            elif isinstance(value, Scope):
                scopes.append(value)
                for scope_key in iterkeys(value.__fields__):
                    pre_fields[scope_key] = to_be_replaced

        for name, field in iteritems(pre_fields):
            if field is to_be_replaced:
                values = []
                for scope in scopes:
                    if name in scope.__fields__:
                        values.append((scope.__matcher__, scope.__fields__[name]))
                fields[name] = Var(values)
            else:
                fields[name] = field

        return fields

    @classmethod
    def collect_options(mcs, bases, attrs):
        """
        Collects options from the current class and its parent classes.

        :returns: a dictionary of options
        """
        options = {}
        # options from parent classes:
        for base in reversed(bases):
            if hasattr(base, '_options'):
                for key, value in inspect.getmembers(base._options):
                    if not key.startswith('_') and value is not None:
                        options[key] = value

        # options from the current class:
        if 'Options' in attrs:
            for key, value in inspect.getmembers(attrs['Options']):
                if not key.startswith('_') and value is not None:
                    # HACK HACK HACK
                    if inspect.ismethod(value) and value.im_self is None:
                        value = value.im_func
                    options[key] = value
        return options

    @classmethod
    def create_options(cls, options):
        """
        Wraps ``options`` into a container class
        (see :attr:`~.DocumentMeta.options_container`).

        :param options: a dictionary of options
        :return: an instance of :attr:`~.DocumentMeta.options_container`
        """
        return cls.options_container(**options)


class Document(with_metaclass(DocumentMeta)):
    """A document. Can be thought as a kind of :class:`.fields.DictField`, which
    properties are defined by the fields and scopes added to the document class.

    It can be tuned using special ``Options`` attribute (see :class:`.Options`
    for available settings)::

        class User(Document):
            class Options(object):
                title = 'User'
                description = 'A person who uses a computer or network service.'
            login = StringField(required=True)
    """

    @classmethod
    def is_recursive(cls, role=DEFAULT_ROLE):
        """Returns ``True`` if there is a :class:`.DocumentField`-references cycle
        that contains ``cls``.

        :param str role: A current role.
        """
        for field in cls.resolve_and_walk(through_document_fields=True,
                                          role=role, visited_documents=set([cls])):
            if isinstance(field, DocumentField):
                if field.document_cls == cls:
                    return True
        return False

    @classmethod
    def get_definition_id(cls, role=DEFAULT_ROLE):
        """Returns a unique string to be used as a key for this document
        in the ``"definitions"`` schema section.
        """
        definition_id = cls._options.definition_id
        if isinstance(definition_id, Resolvable):
            definition_id = definition_id.resolve(role).value
        return definition_id or '{0}.{1}'.format(cls.__module__, cls.__name__)

    @classmethod
    def resolve_field(cls, field, role=DEFAULT_ROLE):
        """Resolves a field with the name ``field`` using ``role``.

        :raises: :class:`AttributeError`
        """
        properties = cls._field.properties
        if field in properties:
            return properties[field].resolve(role)
        else:
            return Resolution(None, role)

    @classmethod
    def resolve_and_iter_fields(cls, role=DEFAULT_ROLE):
        """The same as :meth:`.iter_fields`, but :class:`resolvables <.Resolvable>`
        are resolved using ``role``.
        """
        return cls._field.resolve_and_iter_fields(role=role)

    @classmethod
    def resolve_and_walk(cls, role=DEFAULT_ROLE, through_document_fields=False,
                         visited_documents=frozenset()):
        """The same as :meth:`.walk`, but :class:`resolvables <.Resolvable>` are
        resolved using ``role``.
        """
        fields = cls._field.resolve_and_walk(
            role=role, through_document_fields=through_document_fields,
            visited_documents=visited_documents)
        next(fields)  # we don't want to yield _field itself
        return fields

    @classmethod
    def iter_fields(cls):
        """Iterates over the fields of the document, resolving its
        :class:`resolvables <.Resolvable>` to all possible values.
        """
        return cls._field.iter_fields()

    @classmethod
    def walk(cls, through_document_fields=False, visited_documents=frozenset()):
        """
        Iterates recursively over the fields of the document, resolving
        occurring :class:`resolvables <.Resolvable>` to their all possible values.

        Visits fields in a DFS order.

        :param bool through_document_fields:
            If ``True``, walks through nested :class:`.DocumentField` fields.
        :param set visited_documents:
            Keeps track of visited :class:`documents <.Document>` to avoid infinite
            recursion when ``through_document_field`` is ``True``.
        :returns: iterable of :class:`.BaseField`
        """
        fields = cls._field.walk(through_document_fields=through_document_fields,
                                 visited_documents=visited_documents)
        next(fields)  # we don't want to yield _field itself
        return fields

    @classmethod
    def get_schema(cls, role=DEFAULT_ROLE, ordered=False):
        """Returns a JSON schema (draft v4) of the document.

        :param str role:  A role.
        :param bool ordered:
            If ``True``, the resulting schema dictionary is ordered. Fields are
            listed in the order they are added to the class. Schema properties are
            also ordered in a sensible and consistent way, making the schema more
            human-readable.
        :raises: :class:`.SchemaGenerationException`
        :rtype: dict or OrderedDict
        """
        definitions, schema = cls.get_definitions_and_schema(
            role=role, ordered=ordered,
            res_scope=ResolutionScope(base=cls._options.id, current=cls._options.id)
        )
        rv = OrderedDict() if ordered else {}
        if cls._options.id:
            rv['id'] = cls._options.id
        if cls._options.schema_uri is not None:
            rv['$schema'] = cls._options.schema_uri
        if definitions:
            rv['definitions'] = definitions
        rv.update(schema)
        return rv

    @classmethod
    def get_definitions_and_schema(cls, role=DEFAULT_ROLE, res_scope=ResolutionScope(),
                                   ordered=False, ref_documents=None):
        """Returns a tuple of two elements.

        The second element is a JSON schema of the document, and the first is
        a dictionary that contains definitions that are referenced from the schema.

        :param str role:  A role.
        :param bool ordered:
            If ``True``, the resulting schema dictionary is ordered. Fields are
            listed in the order they are added to the class. Schema properties are
            also ordered in a sensible and consistent way, making the schema more
            human-readable.
        :param res_scope:
            The current resolution scope.
        :type res_scope: :class:`~.ResolutionScope`
        :param set ref_documents:
            If subclass of :class:`.Document` is in this set, all :class:`.DocumentField` s
            pointing to it will be resolved as a reference: ``{"$ref": "#/definitions/..."}``.
            Note: resulting definitions will not contain schema for this document.
        :raises: :class:`~.SchemaGenerationException`
        :rtype: (dict, dict or OrderedDict)
        """
        is_recursive = cls.is_recursive()

        if is_recursive:
            ref_documents = set(ref_documents) if ref_documents else set()
            ref_documents.add(cls)
            res_scope = res_scope.replace(output=res_scope.base)

        with processing(DocumentStep(cls, role=role)):
            definitions, schema = cls._field.get_definitions_and_schema(
                role=role, res_scope=res_scope, ordered=ordered, ref_documents=ref_documents)

        if is_recursive:
            definition_id = cls.get_definition_id()
            definitions[definition_id] = schema
            schema = res_scope.create_ref(definition_id)

        return definitions, schema

# Remove Document itself from registry
registry.remove_document(Document.__name__, module=Document.__module__)
