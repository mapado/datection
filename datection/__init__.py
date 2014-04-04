# -*- coding: utf-8 -*-

"""
Datection provides you with a parser that can extract and normalize
litteral date/time related expressions, from possibly several languages,
and export them into python or database compliant formats.

All expressions will be exported to rrules, as defined in the
RFC 5545: https://tools.ietf.org/html/rfc5545 (prefered for database storage),
and/or python rrules and datetimes objects.
"""

__title__ = 'datection'
__version__ = '1.9.2'
__author__ = 'Balthazar Rouberol'

from datection.parse import parse
from datection.context import probe
from datection.export import to_db, to_python, to_mongo
from datection.display import display
from datection.future import is_future
from datection.similarity import similarity
