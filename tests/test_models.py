import datetime
import os
from .base import unittest
from pyiconfinder.client import Client
from pyiconfinder.models import (
    Category, Style, License, LicenseScope, ModelList,
)


TOTAL_STYLES_COUNT = 9
"""Known total number of styles.
"""


class ModelTestCase(unittest.TestCase):
    """Base model test case.

    :ivar anon_client: Anonymous client.
    :ivar ident_client: Identified client using client ID and secret.
    :ivar nonauth_client:
        Non-authenticated client with highest request rate limit.
    """

    def setUp(self):
        super(ModelTestCase, self).setUp()

        self.anon_client = Client()

        client_id = os.environ.get('ICONFINDER_CLIENT_ID', None)
        client_secret = os.environ.get('ICONFINDER_CLIENT_SECRET', None)

        if client_id:
            self.ident_client = Client(client_id=client_id,
                                       client_secret=client_secret)
            self.nonauth_client = self.ident_client
        else:
            self.nonauth_client = self.anon_client


class ModelDeserializeTestCaseMixin(object):
    """Mixin for testing model deserialization.

    :ivar model_cls: Model class. Must be defined by mixed class.
    :ivar deserialize_fixtures_valid:
        Expectedly valid fixtures for testing model deserialization in the
        format of an iterable of :class:`tuple` of ``(payload, attributes)``
        where ``attributes`` is a :class:`dict` of the expected attributes
        of the deserialized model instance. Must be defined by mixed class.
    :ivar deserialize_fixture_invalid:
        Expectedly invalid fixtures for testing model deserialization in the
        format of an iterable of :class:`tuple` of ``(payload, exception)``
        where ``exception`` is the exception expected to be raised during
        deserialization. Must be defined by mixed class.
    """

    def test_deserialize(self):
        """Model.deserialize(payload)
        """

        # Valid payloads.
        for payload, expected_attrs in self.deserialize_fixtures_valid:
            des = self.model_cls.deserialize(payload)

            for k, v in expected_attrs.items():
                self.assertEqual(getattr(des, k), v)

        # Invalid payloads.
        for payload, exception in self.deserialize_fixtures_invalid:
            with self.assertRaises(exception):
                self.model_cls.deserialize(payload)


class CategoryTestCase(ModelDeserializeTestCaseMixin,
                       ModelTestCase):
    """Test case for :class:`Category` model.
    """

    model_cls = Category
    deserialize_fixtures_valid = [({
        'identifier': 'halloween',
        'name': 'Halloween',
    }, {
        'identifier': 'halloween',
        'name': 'Halloween',
    }, ), ]
    deserialize_fixtures_invalid = [({}, ValueError)]


class StyleTestCase(ModelDeserializeTestCaseMixin,
                    ModelTestCase):
    """Test case for :class:`Style` model.
    """

    model_cls = Style
    deserialize_fixtures_valid = [({
        'identifier': 'glyph',
        'name': 'Glyph',
    }, {
        'identifier': 'glyph',
        'name': 'Glyph',
    }, ), ]
    deserialize_fixtures_invalid = [({}, ValueError)]

    def test_get(self):
        """Style.get(..)
        """

        # Retrieve style non-authenticatedly.
        style = Style.get('glyph', client=self.nonauth_client)
        self.assertIsInstance(style, Style)
        self.assertEqual(style.identifier, 'glyph')
        self.assertEqual(style.name, 'Glyph')
        self.assertIsNotNone(style.http_last_modified)

        # Retrieve style non-authenticatedly through model proxy.
        style = self.nonauth_client.Style.get('handdrawn')
        self.assertIsInstance(style, Style)
        self.assertEqual(style.identifier, 'handdrawn')
        self.assertEqual(style.name, 'Handdrawn')
        self.assertIsNotNone(style.http_last_modified)

        # Test If-Modified-Since behavior.
        #
        # Given that styles very rarely change, this is a pretty safe test
        # case window.
        self.assertIsNone(Style.get(
            'handdrawn',
            client=self.nonauth_client,
            if_modified_since=style.http_last_modified)
        )

        style = Style.get('handdrawn',
                          client=self.nonauth_client,
                          if_modified_since=style.http_last_modified -
                          datetime.timedelta(seconds=1))
        self.assertIsInstance(style, Style)
        self.assertEqual(style.identifier, 'handdrawn')

    def test_list(self):
        """Style.list(..)
        """

        # Retrieve styles.
        all_styles = None

        for kwargs in [{}, {
            'count': 100,
        }, {
            'count': 5,
        }]:
            styles = Style.list(client=self.nonauth_client, **kwargs)
            if all_styles is None:
                all_styles = styles
            self.assertIsInstance(styles, ModelList)
            self.assertEqual(len(styles),
                             min(kwargs.get('count', TOTAL_STYLES_COUNT),
                                 TOTAL_STYLES_COUNT))
            self.assertEqual(styles.total_count, TOTAL_STYLES_COUNT)
            self.assertIsNotNone(styles.last_modified)

            for s in styles:
                self.assertIsInstance(s, Style)

        # Retrieve limited list of styles.
        styles = Style.list(count=3,
                            after=all_styles[1],
                            client=self.nonauth_client)
        self.assertIsInstance(styles, ModelList)
        self.assertEqual(len(styles), 3)
        self.assertEqual(styles[0].identifier, all_styles[2].identifier)
        self.assertEqual(styles[1].identifier, all_styles[3].identifier)
        self.assertEqual(styles[2].identifier, all_styles[4].identifier)


class LicenseTestCase(ModelDeserializeTestCaseMixin,
                      ModelTestCase):
    """Test case for :class:`License` model.
    """

    model_cls = License
    deserialize_fixtures_valid = [({
        'license_id': 5,
        'name': 'Test license',
        'scope': 'free',
    }, {
        'license_id': 5,
        'name': 'Test license',
        'scope': LicenseScope.free,
        'url': None,
    }), ]
    deserialize_fixtures_invalid = [({}, ValueError), ({
        'license_id': '5',
        'name': 'Test license',
        'scope': 'free',
    }, ValueError), ({
        'license_id': 5,
        'name': 'Test license',
        'scope': 'something',
    }, ValueError), ]

    def test_get(self):
        """License.get(..)
        """

        # Retrieve license non-authenticatedly.
        lic = License.get(1, client=self.nonauth_client)
        self.assertIsInstance(lic, License)
        self.assertEqual(lic.license_id, 1)
        self.assertIsNotNone(lic.name)
        self.assertIsNotNone(lic.http_last_modified)

        # Retrieve license non-authenticatedly through model proxy.
        lic = self.nonauth_client.License.get(5)
        self.assertIsInstance(lic, License)
        self.assertEqual(lic.license_id, 5)
        self.assertIsNotNone(lic.name)
        self.assertIsNotNone(lic.http_last_modified)

        # Test If-Modified-Since behavior.
        #
        # Given that licenses very rarely change, this is a pretty safe test
        # case window.
        self.assertIsNone(License.get(
            5,
            client=self.nonauth_client,
            if_modified_since=lic.http_last_modified)
        )

        lic = License.get(5,
                          client=self.nonauth_client,
                          if_modified_since=lic.http_last_modified -
                          datetime.timedelta(seconds=1))
        self.assertIsInstance(lic, License)
        self.assertEqual(lic.license_id, 5)
