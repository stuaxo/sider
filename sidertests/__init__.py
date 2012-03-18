import doctest
from attest import Tests
from . import list
from sider import datetime, types


tests = Tests()
tests.register(list.tests)


@tests.test
def doctest_types():
    assert 0 == doctest.testmod(types)[0]


@tests.test
def doctest_datetime():
    assert 0 == doctest.testmod(datetime)[0]

