import datetime
import pytz
from pyiconfinder.utils import (
    force_datetime_naive_utc,
    http_datetime,
    parse_http_datetime,
)
from .base import unittest


class ForceDatetimeNaiveUtcTestCase(unittest.TestCase):
    """Test case for utility function :func:`force_datetime_naive_utc`.
    """

    def test_force_datetime_naive_utc(self):
        """force_datetime_naive_utc(..)
        """

        for fixture, expected in [
                (datetime.datetime(2012, 1, 1, 15, 32, 23),
                 datetime.datetime(2012, 1, 1, 15, 32, 23)),
                (datetime.datetime(2012, 1, 1, 15, 32, 23, tzinfo=pytz.utc),
                 datetime.datetime(2012, 1, 1, 15, 32, 23)),
                (pytz.timezone('Europe/Copenhagen')
                 .localize(datetime.datetime(2012, 1, 1, 15, 32, 23)),
                 datetime.datetime(2012, 1, 1, 14, 32, 23)),
        ]:
            actual = force_datetime_naive_utc(fixture)
            self.assertEqual(actual, expected)
            self.assertIsNone(actual.tzinfo)


class HttpDatetimeTestCase(unittest.TestCase):
    """Test case for utility function :func:`http_datetime`.
    """

    def test_http_datetime(self):
        """http_datetime(..)
        """

        for fixture, expected in [
                (datetime.datetime(2012, 1, 1, 15, 32, 23),
                 'Sun, 01 Jan 2012 15:32:23 GMT'),
                (datetime.datetime(2012, 1, 1, 15, 32, 23, tzinfo=pytz.utc),
                 'Sun, 01 Jan 2012 15:32:23 GMT'),
                (pytz.timezone('Europe/Copenhagen')
                 .localize(datetime.datetime(2012, 1, 1, 15, 32, 23)),
                 'Sun, 01 Jan 2012 14:32:23 GMT'),
        ]:
            actual = http_datetime(fixture)
            self.assertEqual(actual, expected)


class ParseHttpDatetimeTestCase(unittest.TestCase):
    """Test case for utility function :func:`parse_http_datetime`.
    """

    def test_parse_http_datetime(self):
        """parse_http_datetime(..)
        """

        # Invalid date/times.
        for fixture in [
                '',
                'Sun, 01 Jan 2012 15:32:23'
                'Sun, 01 Jar 2012 15:32:23 GMT',
        ]:
            with self.assertRaises(ValueError):
                parse_http_datetime(fixture)

        # Valid date/times.
        for fixture, expected in [
                ('Sun, 01 Jan 2012 15:32:23 GMT',
                 datetime.datetime(2012, 1, 1, 15, 32, 23)),
        ]:
            actual = parse_http_datetime(fixture)
            self.assertEqual(actual, expected)
