import re
from rpython.rlib.objectmodel import compute_hash
import space

class Object:
    _immutable_fields_ = ['interface', 'custom_interface', 'flag', 'number', 'value', 'contents', 'data', 'string[*]', 'iterator', 'arity', 'methods', 'default', 'cells']
    __slots__ = []
    __attrs__ = []
    # The metaclass here takes care every object will get an interface.
    # So programmer doesn't need to do that.
    class __metaclass__(type):
        def __init__(cls, name, bases, dict):
            if name not in ('Object', 'Interface') and 'interface' not in dict:
                cls.interface = Interface(
                    parent = cls.__bases__[0].interface,
                    name = re.sub("(.)([A-Z]+)", r"\1_\2", name).lower().decode('utf-8'))

    def call(self, argv):
        raise space.OldError(u"cannot call " + self.repr())

    def getitem(self, index):
        raise space.OldError(u"cannot getitem " + self.repr())

    def setitem(self, index, value):
        raise space.OldError(u"cannot setitem " + self.repr())

    def iter(self):
        raise space.OldError(u"cannot iterate " + self.repr())

    def listattr(self):
        listing = []
        for name in self.__class__.interface.methods:
            listing.append(space.String(name))
        return listing

    def getattr(self, index):
        try:
            return BoundMethod(self, index, self.__class__.interface.methods[index])
        except KeyError as e:
            raise space.OldError(u"%s not in %s" % (index, self.repr()))

    def setattr(self, index, value):
        raise space.OldError(u"cannot set %s in %s" % (index, self.repr()))

    def callattr(self, name, argv):
        return self.getattr(name).call(argv)

    def contains(self, obj):
        raise space.OldError(u"%s does not contain " % (self.repr(), obj.repr()))

    def repr(self):
        return u"<%s>" % space.get_interface(self).name

    def hash(self):
        return compute_hash(self)

    def eq(self, other):
        return self is other

    @classmethod
    def instantiator(cls, fn):
        def _instantiate_b_(interface, argv):
            return fn(argv)
        cls.interface.instantiate = _instantiate_b_
        return fn

    @classmethod
    def builtin_method(cls, fn):
        from builtin import Builtin
        builtin = Builtin(fn)
        cls.interface.methods[builtin.name] = builtin

class Interface(Object):
    _immutable_fields_ = ['instantiate?', 'methods']
    # Should add possibility to freeze the interface?
    def __init__(self, parent, name):
        assert isinstance(name, unicode)
        self.parent = parent # TODO: make this matter for custom objects.
        self.name = name
        self.instantiate = None
        self.methods = {}

    def call(self, argv):
        if self.instantiate is None:
            if self.name == u'null':
                raise space.OldError(u"Cannot call null")
            raise space.OldError(u"Cannot instantiate " + self.name)
        return self.instantiate(self, argv)

    def repr(self):
        return self.name

Interface.interface = Interface(None, u"interface")
Interface.interface.parent = Interface.interface

null = Interface(None, u"null")
null.interface = null
null.parent = null

Object.interface = Interface(null, u"object")

class BoundMethod(Object):
    def __init__(self, obj, name, method):
        self.obj = obj
        self.name = name
        self.method = method

    def call(self, argv):
        argv.insert(0, self.obj)
        return self.method.call(argv)

    def repr(self):
        return u"%s.%s" % (self.obj.repr(), self.name)
