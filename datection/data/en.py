# -*- coding: utf-8 -*-

"""English temporal data: weekday names, month names, etc."""

WEEKDAYS = {
    u'monday': 0,
    u'tuesday': 1,
    u'wednesday': 2,
    u'thursday': 3,
    u'friday': 4,
    u'saturday': 5,
    u'sunday': 6,
}

SHORT_WEEKDAYS = {
    u'mon': 0,
    u'tue': 1,
    u'wed': 2,
    u'thu': 3,
    u'fri': 4,
    u'sat': 5,
    u'sun': 6,
}

MONTHS = {
    u'january': 1,
    u'february': 2,
    u'march': 3,
    u'april': 4,
    u'may': 5,
    u'june': 6,
    u'july': 7,
    u'august': 8,
    u'september': 9,
    u'october': 10,
    u'november': 11,
    u'december': 12,
}

SHORT_MONTHS = {
    u'jan': 1,
    u'feb': 2,
    u'mar': 3,
    u'apr': 4,
    u'jun': 6,
    u'jul': 7,
    u'aug': 8,
    u'sep': 9,
    u'oct': 10,
    u'nov': 11,
    u'dec': 12,
}


TRANSLATIONS = {
    'en_US': {
        'today': u"today",
        'today_abbrev': u"today",
        'tomorrow': u'tomorrow',
        'this': u'this',
        'midnight': u'midnight',
        'every day': u'every day',
        'the': u'the',
        'and': u'and',
        'at': u'at',
        'except': u'except',
        'from_day': u'from',
        'to_day': u'to',
        'from_hour': u'from',
        'to_hour': u'to',
    }
}

ORDINAL_APPENDIX = [u'st', u'nd', u'rd', u'th']
TIME_PREPOSITIONS = [u'at']
TIME_CONJUNCTIONS = [u',', u'and', u'&', u'or', u';', u'/']
TIME_INTERVAL_START = [u'from', u'bewteen']
TIME_INTERVAL_MIDDLE = [u'-', u'to', u'and']
DATE_PREPOSITION = [u"on"]
DATE_CONJUNCTIONS = [u'and']
DATE_INTERVAL_START = [u"from", u'bewteen']
DATE_INTERVAL_MIDDLE = [u'to']
DATE_TIME_LINKS = [u',', u'-', u':', u'at']
WEEKLY_LIST_START = [u"on", u"every", u"open on"]
WEEKLY_LIST_MIDDLE = [u';', u',', u'and', u'on', u'&', u'/']
OPEN = u"open"

########################################################
# Patterns and keywords only used for language detection
# (note: some could be used for date parsing)
########################################################
DATE_PATTERNS = {
    u'XX/XX/XXXX',  # uk
    u'XX-XX-XXXX',  # uk
    u'XXXX/XX/XX',  # us
    u'XXXX-XX-XX',  # us
}

ADDITIONAL_KEYWORDS = {
    u'from',
    u'between',
    u'closed',
    u'or',
    u'am',
    u'pm',
}
