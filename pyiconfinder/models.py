import datetime
from enum import Enum
from six import with_metaclass, string_types, integer_types
from .exceptions import (
    UnexpectedResponseError,
)
from .model_proxy import client_dependant_classmethod
from .utils import (
    http_datetime,
    parse_http_datetime,
)


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

        # Determine the primary key.
        primary_key_fields = [a for a, f in fields.items() if f.primary_key]
        if len(primary_key_fields) == 0:
            raise TypeError('model must have a primary key')
        elif len(primary_key_fields) > 1:
            raise TypeError('model cannot have more than one primary key')
        else:
            classdict['__primary_key_attr__'] = primary_key_fields[0]

        # Build the slot list.
        classdict['__slots__'] = tuple(fields.keys()) + (
            '_client',
            'http_last_modified',
        )

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

    @property
    def last_modified(self):
        """Last modification time.

        :returns:
            the last modification time as a time zone naive UTC
            :class:`datetime.datetime` or ``None`` if the last modification
            time is not known.
        """

        if self.http_last_modified:
            return self.http_last_modified
        return None

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

    @property
    def primary_key(self):
        """Primary key.
        """

        return getattr(self, self.__class__.__primary_key_attr__)


class RetrievableModelMixin(object):
    """Retrievable model mixin.
    """

    @client_dependant_classmethod
    def get(cls, id, if_modified_since=None, client=None):
        """Get a resource by its ID.

        :param id: Unique resource ID.
        :param if_modified_since:
            Optional reference to test the against if the resource has been
            modified. Can be either a timestamp as a :class:`datetime.datetime`
            instance or a model instance. If the resource is unmodified since
            the provided timestamp, the call will return ``None``.
        :param client: Optional client to use to perform the request.
        """

        # Construct headers.
        headers = {}
        if if_modified_since is not None:
            if isinstance(if_modified_since, datetime.datetime):
                headers['If-Modified-Since'] = http_datetime(if_modified_since)
            elif isinstance(if_modified_since, cls):
                if cls.last_modified is not None:
                    headers['If-Modified-Since'] = \
                        http_datetime(cls.last_modified)
            else:
                raise TypeError('invalid reference for testing '
                                'modification: %r' % (if_modified_since))

        # Perform the request.
        response = client._api_request('GET',
                                       '%s/%s' % (cls.__endpoint__, id),
                                       headers=headers)

        if response.status_code == 304 and if_modified_since is not None:
            return None
        if response.status_code != 200:
            raise UnexpectedResponseError('unexpected response status code: %d'
                                          % (response.status_code))

        # Deserialize the model.
        model = cls.deserialize(response.json())
        model._client = client

        # Apply available header data.
        if 'last-modified' in response.headers:
            model.http_last_modified = \
                parse_http_datetime(response.headers['last-modified'])

        return model


class ModelList(object):
    """Model list.
    """

    __slots__ = ('_model_cls', '_models', '_total_count', '_last_modified', )

    def __init__(self, model_cls, models, total_count, last_modified=None):
        self._model_cls = model_cls
        self._models = models
        self._total_count = total_count
        self._last_modified = last_modified

    @property
    def total_count(self):
        """Total number of models available from listing endpoint.
        """

        return self._total_count

    @property
    def last_modified(self):
        """Last modification time of the models in the list.

        An instance of :class:`datetime.datetime` if known, otherwise ``None``.
        """

        return self._last_modified

    def __len__(self):
        return len(self._models)

    def __iter__(self):
        return iter(self._models)

    def __getitem__(self, key):
        return self._models[key]

    def __reversed__(self):
        return reversed(self._models)

    def __contains__(self, item):
        return item in self._models

    def __getslice__(self, i, j):
        return self._models[i:j]

    def __repr__(self):
        return '<%s.%s of %s.%s: %r, total count = %d%s>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            self._model_cls.__module__,
            self._model_cls.__name__,
            self._models,
            self._total_count,
            ', last modified = %s' % (self._last_modified
                                      .strftime('%Y-%m-%d %H:%M:%S'))
            if self._last_modified is not None else '',
        )


class ListableByAfterModelMixin(object):
    """Listable by after model mixin.
    """

    @client_dependant_classmethod
    def list(cls, count=10, after=None, if_modified_since=None, client=None):
        """List resources.

        :param count: Number of resources to return. Default 10.
        :param since:
            Unique resource ID or instance after which to list resources.
        :param if_modified_since:
            Optional reference to test the against if the resource has been
            modified. Can be either a timestamp as a :class:`datetime.datetime`
            instance or a model instance. If the resource is unmodified since
            the provided timestamp, the call will return ``None``.
        :param client: Optional client to use to perform the request.
        :returns:
            a :class:`ModelList` instance.
        """

        # Construct headers.
        headers = {}
        if if_modified_since is not None:
            if isinstance(if_modified_since, datetime.datetime):
                headers['If-Modified-Since'] = http_datetime(if_modified_since)
            elif isinstance(if_modified_since, cls):
                if cls.last_modified is not None:
                    headers['If-Modified-Since'] = \
                        http_datetime(cls.last_modified)
            else:
                raise TypeError('invalid reference for testing '
                                'modification: %r' % (if_modified_since))

        # Perform the request.
        params = {}

        if count != 10:
            params['count'] = '%d' % (count)
        if after is not None:
            if isinstance(after, cls):
                params['after'] = after.primary_key
            elif isinstance(after, integer_types + string_types):
                params['after'] = after
            else:
                raise TypeError('invalid resource identifier to list '
                                'resources after: %r' % (after))

        response = client._api_request('GET',
                                       cls.__endpoint__,
                                       params=params,
                                       headers=headers)

        if response.status_code == 304 and if_modified_since is not None:
            return None
        if response.status_code != 200:
            raise UnexpectedResponseError('unexpected response status code: %d'
                                          % (response.status_code))

        # Deserialize the models.
        response_json = response.json()
        last_modified = None

        if 'last-modified' in response.headers:
            last_modified = \
                parse_http_datetime(response.headers['last-modified'])

        return ModelList(cls, [
            cls.deserialize(m) for m in response_json[cls.__plural__]
        ], response_json['total_count'], last_modified=last_modified)


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
        'user_id': IntegerField('user_id', primary_key=True),
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
        'author_id': IntegerField('author_id', primary_key=True),
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

    __fields__ = {
        'identifier': StringField('identifier', primary_key=True),
        'name': StringField('name'),
    }
    __repr_fields__ = ('identifier', 'name', )


class Style(Model, RetrievableModelMixin, ListableByAfterModelMixin):
    """Style.

    :ivar identifier: Identifier.
    :ivar name: Name.
    """

    __fields__ = {
        'identifier': StringField('identifier', primary_key=True),
        'name': StringField('name'),
    }
    __repr_fields__ = ('identifier', 'name', )
    __plural__ = 'styles'
    __endpoint__ = 'styles'


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


class License(Model, RetrievableModelMixin):
    """License.

    :ivar license_id: License ID.
    :ivar name: Name.
    :ivar url: URL to license information.
    :ivar scope: License scope as :class:`LicenseScope`.
    """

    __fields__ = {
        'license_id': IntegerField('license_id', primary_key=True),
        'name': StringField('name'),
        'url': StringField('url', required=False),
        'scope': EnumField('scope', LicenseScope),
    }
    __repr_fields__ = ('license_id', 'name', )
    __endpoint__ = 'licenses'
