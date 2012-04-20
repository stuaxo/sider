from attest import Tests, assert_hook, raises
from .env import NInt, init_session, key
from sider.types import SortedSet


tests = Tests()
tests.context(init_session)

S = frozenset
IntSet = SortedSet(NInt)


@tests.test
def iterate(session):
    set_ = session.set(key('test_sortedset_iterate'),
                       {'a': 3, 'b': 1, 'c': 2},
                       SortedSet)
    assert list(set_) == ['b', 'c', 'a']
    setx = session.set(key('test_sortedsetx_iterate'), {1: 3, 2: 1, 3: 2}, IntSet)
    assert list(setx) == [2, 3, 1]


@tests.test
def length(session):
    set_ = session.set(key('test_sortedset_length'), S('abc'), SortedSet)
    assert len(set_) == 3
    setx = session.set(key('test_sortedsetx_length'), S([1, 2, 3]), IntSet)
    assert len(setx) == 3


@tests.test
def contains(session):
    set_ = session.set(key('test_sortedset_contains'), S('abc'), SortedSet)
    assert 'a' in set_
    assert 'd' not in set_
    setx = session.set(key('test_sortedsetx_contains'), S([1, 2, 3]), IntSet)
    assert 1 in setx
    assert 4 not in setx
    assert '1' not in setx
    assert '4' not in setx


@tests.test
def update(session):
    def reset():
        return session.set(key('test_sortedset_update'), S('abc'), SortedSet)
    set_ = reset()
    set_.update('cde')
    assert S(set_) == S('abcde')
    assert list(set_)[-1] == 'c'
    reset()
    set_.update({'a': 1, 'b': 2, 'd': 1, 'e': 1})
    assert S(set_) == S('abcde')
    assert list(set_)[-1] == 'b'
    reset()
    set_.update(a=1, b=2, d=1, e=1)
    assert S(set_) == S('abcde')
    assert list(set_)[-1] == 'b'
    reset()
    set_.update('cde', {'b': 2, 'd': 5}, c=2)
    assert S(set_) == S('abcde')
    assert list(set_)[-3:] == list('bcd')
    def reset2():
        return session.set(key('test_sortedsetx_update'), S([1, 2, 3]), IntSet)
    setx = reset2()
    setx.update([3, 4, 5])
    assert S(setx) == S([1, 2, 3, 4, 5])
    assert list(setx)[-1] == 3
    reset2()
    setx.update({1: 1, 2: 2, 4: 1, 5: 1})
    assert S(setx) == S([1, 2, 3, 4, 5])
    assert list(setx)[-1] == 2
    reset2()
    setx.update([3, 4, 5], {2: 2, 4: 5, 3: 2})
    assert S(setx) == S([1, 2, 3, 4, 5])
    assert list(setx)[-3:] == [2, 3, 4]
