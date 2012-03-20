""":mod:`sider.set` --- Set objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from __future__ import absolute_import
import collections
from .session import Session
from .types import Bulk, ByteString


class Set(collections.Set):
    """The Python-side representaion of Redis set value.  It behaves
    alike built-in Python :class:`frozenset` object.  More exactly, it
    implements :class:`collections.Set` protocol.

    .. todo::

       The :meth:`__repr__()` method should be implemented.

    .. todo::

       Implement :class:`collections.MutableSet` protocol.

    """

    def __init__(self, session, key, value_type=ByteString):
        if not isinstance(session, Session):
            raise TypeError('session must be a sider.session.Session '
                            'instance, not ' + repr(session))
        self.session = session
        self.key = key
        self.value_type = Bulk.ensure_value_type(value_type,
                                                 parameter='value_type')

    def __iter__(self):
        decode = self.value_type.decode
        for member in self.session.client.smembers(self.key):
            yield decode(member)

    def __len__(self):
        return self.session.client.scard(self.key)

    def __contains__(self, member):
        try:
            data = self.value_type.encode(member)
        except TypeError:
            return False
        return bool(self.session.client.sismember(self.key, data))

    def __eq__(self, operand):
        if isinstance(operand, collections.Set):
            return frozenset(self) == frozenset(operand)
        return False

    def __ne__(self, operand):
        return not (self == operand)

    def __sub__(self, operand):
        if not isinstance(operand, collections.Set):
            raise TypeError('operand for - must be an instance of '
                            'collections.Set, not ' + repr(operand))
        return self.difference(operand)

    def __or__(self, operand):
        if not isinstance(operand, collections.Set):
            raise TypeError('operand for - must be an instance of '
                            'collections.Set, not ' + repr(operand))
        return self.union(operand)

    def __ror__(self, operand):
        return self | operand

    def __and__(self, operand):
        if not isinstance(operand, collections.Set):
            raise TypeError('operand for - must be an instance of '
                            'collections.Set, not ' + repr(operand))
        return self.intersection(operand)

    def __rand__(self, operand):
        return self & operand

    def isdisjoint(self, operand):
        """Tests whether two sets are disjoint or not.

        :param operand: another set to test
        :type operand: :class:`collections.Iterable`
        :returns: ``True`` if two sets have a null intersection
        :rtype: :class:`bool`

        """
        if isinstance(operand, Set) and self.session is operand.session:
            if self.value_type != operand.value_type:
                return True
            for _ in self.session.client.sinter(self.key, operand.key):
                return False
            return True
        dec = self.value_type.decode
        return super(Set, self).isdisjoint(dec(member) for member in operand)

    def difference(self, operand):
        """Gets the relative complement of the ``operand`` set in the set.

        :param operand: another set to get the relative complement
        :type operand: :class:`collections.Iterable`
        :returns: the relative complement
        :rtype: :class:`set`

        """
        if isinstance(operand, Set) and self.session is operand.session:
            if self.value_type != operand.value_type:
                return set(self)
            diff = self.session.client.sdiff(self.key, operand.key)
            decode = self.value_type.decode
            return set(decode(member) for member in diff)
        return set(self).difference(operand)

    def union(self, *sets):
        """Gets the union of the given sets.

        :param \*sets: zero or more operand sets to union.
                       all these must be iterable
        :returns: the union set
        :rtype: :class:`set`

        """
        online_sets = {self.value_type: [self]}
        offline_sets = []
        for operand in sets:
            if (isinstance(operand, Set) and self.session is operand.session):
                group = online_sets.setdefault(operand.value_type, [])
                group.append(operand)
            else:
                offline_sets.append(operand)
        union = set()
        for value_type, group in online_sets.iteritems():
            keys = (s.key for s in group)
            subset = self.session.client.sunion(*keys)
            decode = value_type.decode
            union.update(decode(member) for member in subset)
        for operand in offline_sets:
            union.update(operand)
        return union

    def intersection(self, *sets):
        """Gets the intersection of the given sets.

        :param \*sets: zero or more operand sets to get intersection.
                       all these must be iterable
        :returns: the intersection
        :rtype: :class:`set`

        """
        online_sets = []
        offline_sets = []
        for operand in sets:
            if (isinstance(operand, Set) and self.session is operand.session):
                if self.value_type != operand.value_type:
                    return set()
                online_sets.append(operand)
            else:
                offline_sets.append(operand)
        keys = frozenset(s.key for s in online_sets)
        if keys:
            inter = self.session.client.sinter(self.key, *keys)
            decode = self.value_type.decode
            online = set(decode(m) for m in inter)
        else:
            online = self
        if offline_sets:
            base = offline_sets[0]
            if not isinstance(base, set):
                base = set(base)
            base.intersection_update(online, *offline_sets[1:])
            return base
        return online if isinstance(online, set) else set(online)

    def _raw_update(self, members, pipe):
        key = self.key
        if (isinstance(members, Set) and self.session is members.session and
            self.value_type == members.value_type):
            pipe.sunionstore(key, members.key, key)
        else:
            encode = self.value_type.encode
            data = (encode(v) for v in members)
            if self.session.server_version_info < (2, 4, 0):
                for member in data:
                    pipe.sadd(key, member)
            else:
                pipe.sadd(key, *members)
