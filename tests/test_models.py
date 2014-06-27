import datetime
import os
from .base import unittest
from pyiconfinder.client import Client
from pyiconfinder.exceptions import NotFoundError
from pyiconfinder.models import (
    Author, Category, IconSet, Style, License, LicenseScope, ModelList,
)


TOTAL_STYLES_COUNT = 9
"""Known total number of styles.
"""


TOTAL_CATEGORIES_COUNT = 40
"""Known total number of categories.
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


class AuthorTestCase(ModelDeserializeTestCaseMixin,
                     ModelTestCase):
    """Test case for :class:`Author` model.
    """

    model_cls = Author
    deserialize_fixtures_valid = [({
        'author_id': 1,
        'name': 'Author Name',
        'iconsets_count': 5,
    }, {
        'author_id': 1,
        'name': 'Author Name',
        'iconsets_count': 5,
    }, ), ({
        'author_id': 1,
        'name': 'Author Name',
        'iconsets_count': 5,
        'website_url': 'http://designer.com/',
    }, {
        'author_id': 1,
        'name': 'Author Name',
        'iconsets_count': 5,
        'website_url': 'http://designer.com/',
    }, ), ]
    deserialize_fixtures_invalid = [({}, ValueError), ({
        'author_id': 1,
        'name': 'Author Name',
    }, ValueError)]

    def test_get(self):
        """Author.get(..)
        """

        # Retrieve author non-authenticatedly.
        author = Author.get(15, client=self.nonauth_client)
        self.assertIsInstance(author, Author)
        self.assertEqual(author.author_id, 15)
        self.assertIsNotNone(author.http_last_modified)

        with self.assertRaises(NotFoundError):
            Author.get(99999999, client=self.nonauth_client)

        # Retrieve author non-authenticatedly through model proxy.
        author = self.nonauth_client.Author.get(16)
        self.assertIsInstance(author, Author)
        self.assertEqual(author.author_id, 16)
        self.assertIsNotNone(author.http_last_modified)

        with self.assertRaises(NotFoundError):
            self.nonauth_client.Author.get(99999999)

        # Test If-Modified-Since behavior.
        #
        # Given that categories very rarely change, this is a pretty safe test
        # case window.
        self.assertIsNone(Author.get(
            16,
            client=self.nonauth_client,
            if_modified_since=author.http_last_modified
        ))

        author = Author.get(16,
                            client=self.nonauth_client,
                            if_modified_since=author.http_last_modified -
                            datetime.timedelta(seconds=1))
        self.assertIsInstance(author, Author)
        self.assertEqual(author.author_id, 16)


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

    def test_get(self):
        """Category.get(..)
        """

        # Retrieve category non-authenticatedly.
        category = Category.get('halloween', client=self.nonauth_client)
        self.assertIsInstance(category, Category)
        self.assertEqual(category.identifier, 'halloween')
        self.assertEqual(category.name, 'Halloween')
        self.assertIsNotNone(category.http_last_modified)

        with self.assertRaises(NotFoundError):
            Category.get('horse', client=self.nonauth_client)

        # Retrieve category non-authenticatedly through model proxy.
        category = self.nonauth_client.Category.get('abstract')
        self.assertIsInstance(category, Category)
        self.assertEqual(category.identifier, 'abstract')
        self.assertEqual(category.name, 'Abstract')
        self.assertIsNotNone(category.http_last_modified)

        with self.assertRaises(NotFoundError):
            self.nonauth_client.Category.get('horse')

        # Test If-Modified-Since behavior.
        #
        # Given that categories very rarely change, this is a pretty safe test
        # case window.
        self.assertIsNone(Category.get(
            'abstract',
            client=self.nonauth_client,
            if_modified_since=category.http_last_modified)
        )

        category = Category.get('abstract',
                                client=self.nonauth_client,
                                if_modified_since=category.http_last_modified -
                                datetime.timedelta(seconds=1))
        self.assertIsInstance(category, Category)
        self.assertEqual(category.identifier, 'abstract')

    def test_list(self):
        """Category.list(..)
        """

        # Retrieve categories.
        all_categories = None

        for kwargs in [{}, {
            'count': 100,
        }, {
            'count': 5,
        }]:
            categories = Category.list(client=self.nonauth_client, **kwargs)
            if all_categories is None:
                all_categories = categories
            self.assertIsInstance(categories, ModelList)
            self.assertEqual(len(categories),
                             min(kwargs.get('count', 10),
                                 TOTAL_CATEGORIES_COUNT))
            self.assertEqual(categories.total_count, TOTAL_CATEGORIES_COUNT)
            self.assertIsNotNone(categories.last_modified)

            for s in categories:
                self.assertIsInstance(s, Category)

        # Retrieve limited list of categories.
        categories = Category.list(count=3,
                                   after=all_categories[1],
                                   client=self.nonauth_client)
        self.assertIsInstance(categories, ModelList)
        self.assertEqual(len(categories), 3)
        self.assertEqual(categories[0].identifier,
                         all_categories[2].identifier)
        self.assertEqual(categories[1].identifier,
                         all_categories[3].identifier)
        self.assertEqual(categories[2].identifier,
                         all_categories[4].identifier)


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

        with self.assertRaises(NotFoundError):
            Style.get('horse', client=self.nonauth_client)

        # Retrieve style non-authenticatedly through model proxy.
        style = self.nonauth_client.Style.get('handdrawn')
        self.assertIsInstance(style, Style)
        self.assertEqual(style.identifier, 'handdrawn')
        self.assertEqual(style.name, 'Handdrawn')
        self.assertIsNotNone(style.http_last_modified)

        with self.assertRaises(NotFoundError):
            self.nonauth_client.Style.get('horse')

        # Test If-Modified-Since behavior.
        #
        # Given that styles very rarely change, this is a pretty safe test
        # case window.
        self.assertIsNone(Style.get(
            'handdrawn',
            client=self.nonauth_client,
            if_modified_since=style.http_last_modified
        ))

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
            if_modified_since=lic.http_last_modified
        ))

        lic = License.get(5,
                          client=self.nonauth_client,
                          if_modified_since=lic.http_last_modified -
                          datetime.timedelta(seconds=1))
        self.assertIsInstance(lic, License)
        self.assertEqual(lic.license_id, 5)


class IconSetTestCase(ModelTestCase):
    """Test case for :class:`IconSet` model.
    """

    model_cls = IconSet

    def test_get(self):
        """IconSet.get(..)
        """

        # Test non-existent icon sets.
        with self.assertRaises(NotFoundError):
            IconSet.get('--horse', client=self.nonauth_client)

        with self.assertRaises(NotFoundError):
            self.nonauth_client.IconSet.get('--horse')

        # Test public icon sets.
        for retrieve_id, iconset_id, identifier in [
                # Free icon set by author.
                (15, 15, 'DarkGlass_Reworked'),
                ('DarkGlass_Reworked',
                 15,
                 'DarkGlass_Reworked'),

                # Free icon set by user.
                (1781, 1781, 'streamline-icon-set-free-pack'),
                ('streamline-icon-set-free-pack',
                 1781,
                 'streamline-icon-set-free-pack'),

                # Premium icon set.
                (4835, 4835, 'cat-power-premium'),
                ('cat-power-premium', 4835, 'cat-power-premium'),
        ]:
            # Retrieve icon set non-authenticatedly.
            iconset = IconSet.get(retrieve_id, client=self.nonauth_client)
            self.assertIsInstance(iconset, IconSet)
            self.assertEqual(iconset.iconset_id, iconset_id)
            self.assertEqual(iconset.identifier, identifier)
            self.assertIsNotNone(iconset.http_last_modified)

            # Retrieve icon set non-authenticatedly through model proxy.
            iconset = self.nonauth_client.IconSet.get(retrieve_id)
            self.assertIsInstance(iconset, IconSet)
            self.assertIsNotNone(iconset.http_last_modified)
            self.assertEqual(iconset.iconset_id, iconset_id)
            self.assertEqual(iconset.identifier, identifier)

            # Test If-Modified-Since behavior.
            #
            # Might just break, but in most cases it shouldn't be an issue.
            self.assertIsNone(IconSet.get(
                retrieve_id,
                client=self.nonauth_client,
                if_modified_since=iconset.http_last_modified
            ))

            iconset = IconSet.get(
                retrieve_id,
                client=self.nonauth_client,
                if_modified_since=iconset.http_last_modified -
                datetime.timedelta(seconds=1)
            )
            self.assertIsInstance(iconset, IconSet)
            self.assertEqual(iconset.iconset_id, iconset_id)
            self.assertEqual(iconset.identifier, identifier)
