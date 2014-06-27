import os
import requests
from requests.utils import default_user_agent
from six import string_types
from .exceptions import (
    BadRequestError,
    InvalidParameterError,
    BadCredentialsError,
    NotFoundError,
    RateLimitExceededError,
    InternalServerError,
    PermissionDeniedError,
    InsufficientPermissionsError,
    UnexpectedResponseError,
)
from .model_proxy import ModelClassProxy
from .models import Category, License, Style


DEFAULT_API_URL = 'https://api.iconfinder.com/v2'
"""Default API base URL.
"""

DEFAULT_SITE_URL = 'https://www.iconfinder.com'
"""Default site URL.
"""

CA_BUNDLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'wildcard.iconfinder.com.pem')
"""CA bundle path for Iconfinder's wildcard SSL certificate.
"""


class Client(object):
    """Iconfinder API client.

    :ivar License:
        Proxied access to the :class:`License` model using the client.
    """

    def __init__(self,
                 client_id=None,
                 client_secret=None,
                 api_base_url=DEFAULT_API_URL,
                 api_ssl_verify=CA_BUNDLE_PATH,
                 site_base_url=DEFAULT_SITE_URL,
                 site_ssl_verify=CA_BUNDLE_PATH):
        """Initialize an Iconfinder API client.

        Note that if :param:`client_id` is provided, :param:`client_secret`
        must also be provided and vice versa.

        :param client_id: Optional client ID. Default ``None``.
        :param client_secret: Optional client secret. Default ``None``.
        :param api_base_url:
            API base URL. Default ``https://api.iconfinder.com/v2``.
        :param api_ssl_verify:
            API SSL verification. Refer to the `Requests documentation
            <http://docs.python-requests.org/>`_ for further details. Defaults
            to the included CA bundle for the Iconfinder wildcard SSL
            certificate.
        :param site_url: Site base URL. Default ``https://www.iconfinder.com``.
        :param site_ssl_verify:
            Site SSL verification. Refer to the `Requests documentation
            <http://docs.python-requests.org/>`_ for further details. Defaults
            to the included CA bundle for the Iconfinder wildcard SSL
            certificate.
        """

        # Validate client ID and secret.
        if (client_id is None) != (client_secret is None):
            raise ValueError('client_id and client_secret must both be '
                             'provided if one is provided')
        if client_id is not None and not isinstance(client_id, string_types):
            raise TypeError('client_id must be a string value')
        if client_secret is not None and \
           not isinstance(client_secret, string_types):
            raise TypeError('client_secret must be a string value')

        self._client_id = client_id or None
        self._client_secret = client_secret or None

        # Set up URLs etc.
        self._api_base_url = api_base_url.rstrip('/')
        self._api_ssl_verify = api_ssl_verify
        self._site_base_url = site_base_url.rstrip('/')
        self._site_ssl_verify = site_ssl_verify

        # Set up sessions.
        from . import __version__
        user_agent = 'pyiconfinder/%s %s' % (__version__, default_user_agent())

        self._api_session = requests.Session()
        self._api_session.verify = api_ssl_verify
        self._api_session.headers['User-Agent'] = user_agent

        self._site_session = requests.Session()
        self._site_session.verify = site_ssl_verify
        self._site_session.headers['User-Agent'] = user_agent

        # Set up model class proxies.
        self.Category = ModelClassProxy(Category, self)
        self.License = ModelClassProxy(License, self)
        self.Style = ModelClassProxy(Style, self)

    @property
    def client_id(self):
        """Client ID.
        """

        return self._client_id

    @property
    def client_secret(self):
        """Client secret.
        """

        return self._client_secret

    @property
    def api_base_url(self):
        """API base URL.
        """

        return self._api_base_url

    @property
    def api_ssl_verify(self):
        """API SSL verification.

        Refer to the `Requests documentation
        <http://docs.python-requests.org/>`_ for details on the meaning of the
        value.
        """

        return self._api_ssl_verify

    @property
    def site_base_url(self):
        """Site base URL.
        """

        return self._site_base_url

    @property
    def site_ssl_verify(self):
        """Site SSL verification.

        Refer to the `Requests documentation
        <http://docs.python-requests.org/>`_ for details on the meaning of the
        value.
        """

        return self._site_ssl_verify

    def _api_url(self, relative_url):
        """Construct API URL from relative endpoint URL.

        :param relative_url: Endpoint URL relative to the API base URL.
        :returns: the fully qualified URL for the API endpoint.
        """

        return '%s/%s' % (self._api_base_url, relative_url.lstrip('/'))

    def _api_request(self,
                     method,
                     relative_url,
                     params=None,
                     data=None,
                     headers=None):
        """Perform a request against the API.

        :param method: Request method.
        :param relative_url: Endpoint URL relative to the API base URL.
        :param params: Optional request query parameters as a :class:`dict`.
        :param data:
            Optional :class:`dict` or bytes to send in the body of the request.
        :param headers:
            Optional :class:`dict` of headers to send with the request.
        :returns: the response from the API.
        """

        # Assign the client ID and secret to the request if available, to
        # utilize the higher request rate limit.
        if self.client_id:
            if params is None:
                params = {}

            params['client_id'] = self.client_id
            params['client_secret'] = self.client_secret

        # Perform the actual request.
        response = self._api_session.request(method,
                                             self._api_url(relative_url),
                                             params=params,
                                             data=data,
                                             headers=headers,
                                             allow_redirects=False)

        # Check the response status code for errors.
        if response.status_code >= 400:
            # Attempt to parse the error.
            error_code = None
            error_message = None

            try:
                error_json = response.json()
                error_code = error_json['code']
                error_message = error_json['message']
            except:
                pass

            # Handle specific errors depending on the status code and error
            # codes.
            if response.status_code == 400:
                if error_code.startswith('invalid_'):
                    raise InvalidParameterError(
                        error_message or 'invalid parameter',
                        error_code[len('invalid_'):]
                    )
                raise BadRequestError(error_message or 'bad request')
            if response.status_code == 401:
                raise BadCredentialsError(error_message or 'bad credentials')
            if response.status_code == 403:
                if error_code == 'insufficient_permissions':
                    raise InsufficientPermissionsError(
                        error_message or
                        'insufficient permissions to access the requested '
                        'resource'
                    )
                raise PermissionDeniedError(
                    error_message or
                    'permission to the requested resource was denied'
                )
            if response.status_code == 404:
                raise NotFoundError(error_message or
                                    'the requested resource was not found')
            if response.status_code == 429:
                raise RateLimitExceededError(error_message or
                                             'request rate limit exceeded')
            if response.status_code == 500:
                raise InternalServerError(error_message or
                                          'internal server error')

            raise UnexpectedResponseError('unexpected response with status '
                                          'code %d' % (response.status_code))

        return response
