import datetime
import re
import sys
from email.utils import formatdate


class Utc(datetime.tzinfo):
    """UTC time zone information.

    Taken from Python's docs.
    """

    def __repr__(self):
        return "<UTC>"

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)


utc = Utc()
"""Global UTC time zone instance.
"""


UNIX_EPOCH = datetime.datetime(1970, 1, 1)
"""UNIX epoch.
"""


MONTHS_MAP = {
    k: i + 1 for i, k in enumerate([
        'jan', 'feb', 'mar', 'apr', 'may', 'jun',
        'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
    ])
}
"""Month mapping.
"""


RFC1123_DATE = re.compile(r'^\w{3}, (?P<day>\d{2}) (?P<month>\w{3}) '
                          r'(?P<year>\d{4}) '
                          r'(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2}) '
                          r'GMT$')
"""RFC 1123 date format.
"""


if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    def timedelta_total_seconds(td):
        return ((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6)
                / 10**6)
else:
    def timedelta_total_seconds(td):
        return td.total_seconds()


def force_datetime_naive_utc(value):
    """Force a :class:`datetime.datetime` instance to be naive UTC.
    """

    if value.tzinfo:
        return value.astimezone(utc).replace(tzinfo=None)
    return value


def http_datetime(timestamp):
    """Convert a :class:`datetime.datetime` instance to HTTP date/time.

    :returns:
        the RFC1123 representation of the date/time as specified in RFC2616
        section 3.3.1.
    """

    return formatdate(
        timedelta_total_seconds(force_datetime_naive_utc(timestamp) -
                                UNIX_EPOCH),
        usegmt=True
    )


def parse_http_datetime(value):
    """Parse an HTTP date/time to :class:`datetime.datetime`.

    Expects the HTTP date/time to be in the RFC1123 format for simplicity, as
    we guarantee this is the case from the Iconfinder API.

    :raises ValueError: if the supplied value is not a valid RFC1123 date/time.
    :returns:
        the parsed date/time as a naive :class:`datetime.datetime` instance in
        UTC.
    """

    match = RFC1123_DATE.match(value)
    if not match:
        raise ValueError('%r is not a valid RFC1123 date/time' % (value))

    try:
        month = MONTHS_MAP[match.group('month').lower()]
    except KeyError:
        raise ValueError('%s is not a valid month abbrevation' %
                         (match.group('month')))

    return datetime.datetime(int(match.group('year')),
                             month,
                             int(match.group('day')),
                             int(match.group('hour')),
                             int(match.group('min')),
                             int(match.group('sec')))
