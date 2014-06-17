from functools import partial


_special_names = [
    '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
    '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
    '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
    '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__',
    '__iand__', '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__',
    '__imod__',  '__imul__', '__int__', '__invert__', '__ior__',
    '__ipow__', '__irshift__', '__isub__', '__iter__', '__itruediv__',
    '__ixor__', '__le__', '__len__', '__long__', '__lshift__', '__lt__',
    '__mod__', '__mul__', '__ne__', '__neg__', '__oct__', '__or__',
    '__pos__', '__pow__', '__radd__', '__rand__', '__rdiv__',
    '__rdivmod__', '__reduce__', '__reduce_ex__', '__reversed__',
    '__rfloorfiv__', '__rlshift__', '__rmod__', '__rmul__', '__ror__',
    '__rpow__', '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__',
    '__rxor__', '__setitem__', '__setslice__', '__sub__', '__truediv__',
    '__xor__', 'next',
]


class ModelClassProxy(object):
    """Model class proxy for clients.

    Wraps client-dependant methods as partial methods with the client assigned.
    """

    @classmethod
    def _create_class_proxy(cls, proxy_cls):
        """creates a proxy for the given class"""

        def make_method(name):
            def method(self, *args, **kwargs):
                attr = getattr(object.__getattribute__(self, "_model_cls"),
                               name)
                return attr(*args, **kwargs)
            return method

        namespace = {}
        for name in _special_names:
            if hasattr(proxy_cls, name):
                namespace[name] = make_method(name)
        return type("%s(%s)" % (cls.__name__, proxy_cls.__name__),
                    (cls, ),
                    namespace)

    def __new__(cls, obj, *args, **kwargs):
        try:
            cache = cls.__dict__['_class_proxy_cache']
        except KeyError:
            cls._class_proxy_cache = cache = {}
        try:
            proxy_cls = cache[obj.__class__]
        except KeyError:
            cache[obj.__class__] = proxy_cls = \
                cls._create_class_proxy(obj.__class__)
        ins = object.__new__(proxy_cls)
        proxy_cls.__init__(ins, obj, *args, **kwargs)
        return ins

    def __init__(self, model_cls, client):
        """Initialize model proxy.

        :param model_cls: Model class.
        :param client: Client.
        """

        self._model_cls = model_cls
        self._client = client

    def __getattribute__(self, name):
        attr = getattr(object.__getattribute__(self, "_model_cls"), name)
        if getattr(attr, 'client_dependant', None) is True:
            return partial(attr,
                           client=object.__getattribute__(self, "_client"))
        return attr

    def __str__(self):
        return str(object.__getattribute__(self, "_model_cls"))

    def __repr__(self):
        model_cls = object.__getattribute__(self, "_model_cls")
        return '<%s.%s proxied for client>' % (model_cls.__module__,
                                               model_cls.__name__)


def client_dependant_classmethod(f):
    """Client dependant class method decorator.

    Expects the last argument to the method to be named ``client``.
    """

    f.client_dependant = True
    return classmethod(f)
