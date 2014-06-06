import sys


if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    import unittest2 as unittest
else:
    import unittest


__all__ = (
    unittest.__name__,
)
