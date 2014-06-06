from enum import Enum
from six import with_metaclass, string_types, integer_types


class Field(object):
    """Model field.

    Abstract base class.
    """

    def __init__(self, name, required=True):
        self.name = name
        self.required = required


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
    def deserialize(self, payload):
        value = payload.get(self.name, None)

        if value is None and self.required:
            raise ValueError('expected field %s to be present in payload' %
                             (self.name))
        elif value is not None and not isinstance(value, integer_types):
            raise ValueError('expected field %s to be an integer, but it is '
                             '%r: %r' % (self.name, type(value), value))

        return value


class BooleanField(Field):
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


class ModelMeta(type):
    """Model meta calss.
    """

    def __new__(metacls, cls, bases, classdict):
        # Classes without a ``__fields__`` attribute are considered abstract
        # base classes.
        if '__fields__' not in classdict:
            return super(ModelMeta, metacls) \
                .__new__(metacls, cls, bases, classdict)

        fields = classdict['__fields__']

        # Build the slot list.
        classdict['__slots__'] = fields.keys()

        # Return the final model class.
        model_cls = super(ModelMeta, metacls) \
            .__new__(metacls, cls, bases, classdict)
        return model_cls


class Model(with_metaclass(ModelMeta, object)):
    """Model base class.

    Implementations must have a ``__fields__`` class attribute containing a
    :class:`dict` mapping instance attribute names to field representations.
    Implementations should also have a ``__repr_fields__`` :class:`tuple`
    containing the instance attribute names to be listed in instance
    representations.
    """

    def __repr__(self):
        return '<%s.%s%s>' % (self.__module__,
                              self.__class__.__name__,
                              (': %s' % (', '.join([
                                  '%s = %s' % (name, getattr(self, name))
                                  for name in self.__repr_fields__
                              ])))
                              if getattr(self, '__repr_fields__', None)
                              else '')

    @classmethod
    def deserialize(cls, payload):
        """Deserialize a payload.

        :param payload: Payload to deserialize.
        :returns: an instance of the model with the payload deserialized.
        """

        des = cls()

        for name, field in cls.__fields__.items():
            setattr(des, name, field.deserialize(payload))

        return des


class User(Model):
    """User.

    :ivar user_id: User ID.
    :ivar username: Username.
    :ivar location: Location.
    :ivar name: Name.
    :ivar social_twitter: Twitter handle.
    :ivar social_dribbble: dribbble handle.
    :ivar social_behance: Behance portfolio URL.
    :ivar website_url: Website URL.
    :ivar company: Company.
    :ivar is_designer: Whether the user is a designer.
    :ivar iconsets_count: Number of icon sets owned by the user.
    :ivar email: E-mail address. Only available for authenticated users.
    :ivar first_name: First name. Only available for authenticated users.
    :ivar last_name: Last name. Only available for authenticated users.
    """

    __fields__ = {
        'user_id': IntegerField('user_id'),
        'username': StringField('username'),
        'location': StringField('location', required=False),
        'name': StringField('name'),
        'social_twitter': StringField('social_twitter', required=False),
        'social_dribbble': StringField('social_dribbble', required=False),
        'social_behance': StringField('social_behance', required=False),
        'website_url': StringField('website_url', required=False),
        'company': StringField('company', required=False),
        'is_designer': BooleanField('is_designer'),
        'iconsets_count': IntegerField('iconsets_count'),
        'email': StringField('email', required=False),
        'first_name': StringField('first_name', required=False),
        'last_name': StringField('last_name', required=False),
    }
    __repr_fields__ = ('user_id', 'username', )


class Author(Model):
    """Author.

    :ivar author_id: Author ID.
    :ivar name: Name.
    :ivar website_url: Website URL.
    :ivar iconsets_count: Number of icon sets owned by the user.
    """

    __fields__ = {
        'author_id': IntegerField('author_id'),
        'name': StringField('name'),
        'website_url': StringField('website_url'),
        'iconsets_count': IntegerField('iconsets_count'),
    }
    __repr_fields__ = ('author_id', 'name', )


class Category(Model):
    """Category.

    :ivar identifier: Identifier.
    :ivar name: Name.
    """

    __fields = {
        'identifier': StringField('identifier'),
        'name': StringField('name'),
    }
    __repr_fields__ = ('identifier', 'name', )


class Style(Model):
    """Style.

    :ivar identifier: Identifier.
    :ivar name: Name.
    """

    __fields = {
        'identifier': StringField('identifier'),
        'name': StringField('name'),
    }
    __repr_fields__ = ('identifier', 'name', )


class LicenseScope(Enum):
    """License scope.
    """

    free = 'free'
    """Free.
    """

    free_with_attribution = 'attribution'
    """Free with attribution.
    """

    commercial = 'commercial'
    """Commercial.
    """


class License(Model):
    """License.

    :ivar license_id: License ID.
    :ivar name: Name.
    :ivar url: URL to license information.
    :ivar scope: License scope as :class:`LicenseScope`.
    """

    __fields__ = {
        'license_id': IntegerField('license_id'),
        'name': StringField('name'),
        'url': StringField('url', required=False),
        'scope': EnumField('scope', LicenseScope),
    }
    __repr_fields__ = ('license_id', 'name', )
