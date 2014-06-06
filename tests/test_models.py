from unittest import TestCase
from pyiconfinder.models import License, LicenseScope


class LicenseTestCase(TestCase):
    """Test case for :class:`License` model.
    """

    def test_deserialize(self):
        """License.deserialize(payload)
        """

        # Valid payloads.
        for license_id, name, url, scope, payload in [
                (5, 'Test license', None, LicenseScope.free, {
                    'license_id': 5,
                    'name': 'Test license',
                    'scope': 'free',
                }),
                (5,
                 'Test license',
                 'https://license.org/',
                 LicenseScope.free, {
                     'license_id': 5,
                     'name': 'Test license',
                     'url': 'https://license.org/',
                     'scope': 'free',
                 }),
        ]:
            des = License.deserialize(payload)
            self.assertEqual(des.license_id, license_id)
            self.assertEqual(des.name, name)
            self.assertEqual(des.url, url)
            self.assertEqual(des.scope, scope)

        # Invalid payloads.
        for exception, payload in [
                (ValueError, {
                    'license_id': '5',
                }),
        ]:
            with self.assertRaises(exception):
                License.deserialize(payload)
