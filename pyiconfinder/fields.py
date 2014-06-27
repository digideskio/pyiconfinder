import aniso8601
import datetime
from six import string_types, integer_types


class Field(object):
    """Model field.

    Abstract base class.
    """

    def __init__(self, name, required=True, primary_key=False):
        self.name = name
        self.required = required
        self.primary_key = primary_key


class StringField(Field):
    """String model field.
    """

    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        elif value is not None and not isinstance(value, string_types):
            raise ValueError('expected field %s to be a string, but it is '
                             '%r: %r' % (self.name, type(value), value))

        return value


class IntegerField(Field):
    """Integer model field.
    """

    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        elif value is not None and not isinstance(value, integer_types):
            raise ValueError('expected field %s to be an integer, but it is '
                             '%r: %r' % (self.name, type(value), value))

        return value


class FloatField(Field):
    """Floating point model field.
    """

    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        elif value is not None and not isinstance(value, float):
            raise ValueError('expected field %s to be a floating point '
                             'number, but it is %r: %r' %
                             (self.name, type(value), value))

        return value


class BooleanField(Field):
    """Boolean model field.
    """

    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        if value is not None and not isinstance(value, bool):
            raise ValueError('expected field %s to be a boolean, but it is '
                             '%r: %r' % (self.name, type(value), value))

        return value


class EnumField(Field):
    """Enumeration model .field.

    Translates between a string value and :class:`Enum`.
    """

    def __init__(self, name, enum_cls, required=True):
        super(EnumField, self).__init__(name, required)
        self.enum_cls = enum_cls

    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        if value is not None:
            return self.enum_cls(value)

        return value


class DateTimeField(Field):
    """Date/time model field.
    """

    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        elif value is not None and not isinstance(value, string_types):
            raise TypeError('expected field %s to be a string, but it is '
                            '%r: %r' % (self.name, type(value), value))

        if value is None:
            return None

        value = aniso8601.parse_datetime(value)

        if value.tzinfo is not None:
            utc_offset = value.tzinfo.utcoffset(value)
            dst = value.tzinfo.dst(value)

            if (utc_offset is not None and
                utc_offset != datetime.timedelta(seconds=0)) or \
                (dst is not None and
                 dst != datetime.timedelta(seconds=0)):
                raise ValueError('expected date/time to be UTC based')

            value = value.replace(tzinfo=None)

        return value


class NestedModelField(Field):
    """Nested model field.
    """

    def __init__(self, name, model_cls, required=True):
        super(NestedModelField, self).__init__(name, required)
        self.model_cls = model_cls

    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        if value is None:
            return None

        if not isinstance(value, dict):
            raise ValueError('expected field %s to be a JSON object: %r' %
                             (self.name, value))

        return self.model_cls.deserialize(value)


class NestedModelListField(Field):
    """Nested model list field.
    """

    def __init__(self, name, model_cls, required=True):
        super(NestedModelListField, self).__init__(name, required)
        self.model_cls = model_cls

    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        if value is None:
            return None

        if not isinstance(value, (list, tuple)):
            raise ValueError('expected field %s to be a JSON array: %r' %
                             (self.name, value))

        result = []
        for element in value:
            if not isinstance(element, dict):
                raise ValueError('expected elements of %s to be a JSON '
                                 'object: %r' % (self.name, element))

            result.append(self.model_cls.deserialize(element))

        return result


class UserOrAuthorField(Field):
    """Specialized user or author field.
    """

    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        if value is None:
            return None

        if not isinstance(value, dict):
            raise ValueError('expected field %s to be a JSON object: %r' %
                             (self.name, value))

        from .models import User, Author

        if 'user_id' in value:
            return User.deserialize(value)
        if 'author_id' in value:
            return Author.deserialize(value)

        raise ValueError('unable to determine model of field %s: %r' %
                         (self.name, value))
