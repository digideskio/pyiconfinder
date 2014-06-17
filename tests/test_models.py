import datetime
import os
from .base import unittest
from pyiconfinder.client import Client
from pyiconfinder.models import (
    Category, Style, License, LicenseScope,
)


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
