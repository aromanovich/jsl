import pytest

from jsl.document import Document
from jsl.fields import (ArrayField, StringField, IntField, BaseSchemaField,
                        DictField, OneOfField, AnyOfField, AllOfField, NotField,
                        DocumentField)
from jsl.roles import DEFAULT_ROLE, Var
from jsl.exceptions import (SchemaGenerationException, FieldStep, AttributeStep,
                            ItemStep, DocumentStep)
from jsl.resolutionscope import EMPTY_SCOPE


class FieldStub(BaseSchemaField):
    ERROR_MESSAGE = 'FieldStub error'

    def get_definitions_and_schema(self, role=DEFAULT_ROLE, res_scope=EMPTY_SCOPE,
                                   ordered=False, ref_documents=None):
        raise SchemaGenerationException(self.ERROR_MESSAGE)


def test_exceptions():
    f_1 = StringField()
    f_2 = StringField()

    # test __eq__ and __ne__
    assert FieldStep(f_1) == FieldStep(f_1)
    assert FieldStep(f_1, role='role_1') != FieldStep(f_1)
    assert FieldStep(f_1) != FieldStep(f_2)
    assert FieldStep(f_1) != AttributeStep('fields')
    assert not (FieldStep(f_1) == AttributeStep('fields'))

    # test __repr__
    r = repr(FieldStep(f_1, role='role_1'))
    assert repr(f_1) in r
    assert 'role_1' in r

    message = 'Something went wrong'
    e = SchemaGenerationException(message)
    assert str(e) == message

    step = FieldStep(f_1)
    e.steps.appendleft(step)
    assert str(e) == '{0}\nSteps: {1}'.format(message, step)


def test_error():
    db_role_friends_field = ArrayField((StringField(), None))
    request_role_friends_field = ArrayField(StringField())

    class User(Document):
        login = StringField()
        friends = ArrayField(Var({
            'db_role': db_role_friends_field,
            'request_role': request_role_friends_field,
        }))

    class Users(Document):
        users = ArrayField(DocumentField(User))

    Users.get_schema()

    role = 'db_role'
    with pytest.raises(SchemaGenerationException) as e:
        Users.get_schema(role=role)
    e = e.value

    assert list(e.steps) == [
        DocumentStep(Users, role=role),
        FieldStep(Users._field, role=role),
        AttributeStep('properties', role=role),
        ItemStep('users', role=role),
        FieldStep(Users.users, role=role),
        AttributeStep('items', role=role),
        FieldStep(Users.users.items, role=role),
        DocumentStep(User, role=role),
        FieldStep(User._field, role=role),
        AttributeStep('properties', role=role),
        ItemStep('friends', role=role),
        FieldStep(User.friends, role=role),
        AttributeStep('items', role=role),
        FieldStep(db_role_friends_field, role=role),
        AttributeStep('items', role=role),
        ItemStep(1, role=role)
    ]
    assert e.message == 'None is not resolvable'
    assert ("Steps: Users -> DictField.properties['users'] -> "
            "ArrayField.items -> DocumentField -> User -> "
            "DictField.properties['friends'] -> ArrayField.items -> "
            "ArrayField.items[1]") in str(e)


def test_array_field():
    f = ArrayField(items=())
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    assert list(e.value.steps) == [FieldStep(f), AttributeStep('items')]

    f = ArrayField(items=(
        Var({'role_x': StringField()}),
        Var({'role_x': IntField()}),
    ))
    role = 'role_y'
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema(role='role_y')
    assert list(e.value.steps) == [FieldStep(f, role=role), AttributeStep('items', role=role)]

    f = ArrayField(items=(None, None))
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    assert list(e.value.steps) == [FieldStep(f), AttributeStep('items'), ItemStep(0)]

    f = ArrayField(items=object())
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    assert list(e.value.steps) == [FieldStep(f), AttributeStep('items')]

    f = ArrayField(additional_items=object())
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    assert list(e.value.steps) == [FieldStep(f), AttributeStep('additional_items')]

    f = ArrayField(items=FieldStub())
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert e.message == FieldStub.ERROR_MESSAGE
    assert list(e.steps) == [FieldStep(f), AttributeStep('items')]

    f = ArrayField(items=(FieldStub(),))
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert e.message == FieldStub.ERROR_MESSAGE
    assert list(e.steps) == [FieldStep(f), AttributeStep('items'), ItemStep(0)]

    f = ArrayField(additional_items=FieldStub())
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert e.message == FieldStub.ERROR_MESSAGE
    assert list(e.steps) == [FieldStep(f), AttributeStep('additional_items')]


def test_dict_field():
    f = DictField(properties={'a': object()})
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert 'not resolvable' in e.message
    assert list(e.steps) == [FieldStep(f), AttributeStep('properties'), ItemStep('a')]

    f = DictField(pattern_properties={'a.*': object()})
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert 'not resolvable' in e.message
    assert list(e.steps) == [FieldStep(f), AttributeStep('pattern_properties'), ItemStep('a.*')]

    f = DictField(additional_properties=object())
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert 'not a BaseField or a bool' in e.message
    assert list(e.steps) == [FieldStep(f), AttributeStep('additional_properties')]

    f = DictField(properties={'a': FieldStub()})
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert e.message == FieldStub.ERROR_MESSAGE
    assert list(e.steps) == [FieldStep(f), AttributeStep('properties'), ItemStep('a')]

    f = DictField(pattern_properties={'a.*': FieldStub()})
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert e.message == FieldStub.ERROR_MESSAGE
    assert list(e.steps) == [FieldStep(f), AttributeStep('pattern_properties'), ItemStep('a.*')]

    f = DictField(additional_properties=FieldStub())
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert e.message == FieldStub.ERROR_MESSAGE
    assert list(e.steps) == [FieldStep(f), AttributeStep('additional_properties')]

    for kwarg_value in (object(), Var({'role_x': object()})):
        for kwarg in ('properties', 'pattern_properties'):
            f = DictField(**{kwarg: kwarg_value})
            with pytest.raises(SchemaGenerationException) as e:
                f.get_schema(role='role_x')
            e = e.value
            assert 'not a dict' in e.message
            assert list(e.steps) == [FieldStep(f, role='role_x'),
                                     AttributeStep(kwarg, role='role_x')]

        f = DictField(additional_properties=kwarg_value)
        with pytest.raises(SchemaGenerationException) as e:
            f.get_schema(role='role_x')
        e = e.value
        assert 'not a BaseField or a bool' in e.message
        assert list(e.steps) == [FieldStep(f, role='role_x'),
                                 AttributeStep('additional_properties', role='role_x')]

    f = DictField(pattern_properties={'((((': StringField()})
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert 'unbalanced parenthesis' in e.message
    assert list(e.steps) == [FieldStep(f), AttributeStep('pattern_properties')]


@pytest.mark.parametrize('field_cls', [OneOfField, AnyOfField, AllOfField])
def test_keyword_of_fields(field_cls):
    f = field_cls(object())
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert 'not a list or a tuple' in e.message
    assert list(e.steps) == [FieldStep(f), AttributeStep('fields')]

    f = field_cls([])
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert 'empty' in e.message
    assert list(e.steps) == [FieldStep(f), AttributeStep('fields')]

    f = field_cls([object()])
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert 'not resolvable' in e.message
    assert list(e.steps) == [FieldStep(f), AttributeStep('fields'), ItemStep(0)]

    role = 'role_x'
    f = field_cls([Var({role: object()})])
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema(role=role)
    e = e.value
    assert 'not a BaseField' in e.message
    assert list(e.steps) == [FieldStep(f, role),
                             AttributeStep('fields', role),
                             ItemStep(0, role)]

    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert 'empty' in e.message
    assert list(e.steps) == [FieldStep(f), AttributeStep('fields')]

    # test nested field errors
    f = field_cls([FieldStub()])
    with pytest.raises(SchemaGenerationException) as e:
        f.get_schema()
    e = e.value
    assert e.message == FieldStub.ERROR_MESSAGE
    assert list(e.steps) == [FieldStep(f), AttributeStep('fields'), ItemStep(0)]


def test_not_field():
    for f in [NotField(object()), NotField(Var({'role_x': object()}))]:
        with pytest.raises(SchemaGenerationException) as e:
            f.get_schema()
        e = e.value
        assert 'not a BaseField' in e.message
        assert list(e.steps) == [FieldStep(f), AttributeStep('field')]
