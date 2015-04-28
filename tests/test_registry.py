# coding: utf-8
import pytest

from jsl import registry


def test_registry():
    registry.clear()

    assert not list(registry.iter_documents())

    a = object()
    registry.put_document('A', a, module='qwe.rty')
    assert registry.get_document('qwe.rty.A') is a

    b = object()
    registry.put_document('B', b)
    assert registry.get_document('B') is b

    assert set(registry.iter_documents()) == set([a, b])

    registry.remove_document('B')

    assert set(registry.iter_documents()) == set([a])

    with pytest.raises(KeyError):
        registry.remove_document('A')

    registry.remove_document('A', module='qwe.rty')
