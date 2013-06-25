# -*- coding: utf-8 -*-

"""
Datection provides you with a parser that can extract, serialize and
serialize date/time related expressions.

For example, the french expression "le lundi 15 mars, de 15h30 à 16h"
will be normalized into the following JSON structure:
{
    'date': {'day': 15, 'month': 3, 'year': None},
    'time':
        {'end_time': {'hour': 16, 'minute': 0},
        'start_time': {'hour': 15,'minute': 30}
        }
},
and the following python standard (and SQL-compliant) structure
(
    datetime.datetime(2013, 3, 15, 15, 30),
    datetime.datetime(2013, 3, 15, 16, 0)
)

No external dependencies are required.
"""

__title__ = 'datection'
__version__ = '0.6.2'
__author__ = 'Balthazar Rouberol'

from datection.parse import parse
from datection.context import probe
from datection.export import to_db, to_python, to_mongo
from datection.future import is_future, filter_future
from datection.display import display
