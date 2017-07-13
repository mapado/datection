# -*- coding: utf-8 -*-

"""Flemish temporal data: weekday names, month names, etc."""

WEEKDAYS = {
    u'maandag': 0,
    u'dinsdag': 1,
    u'woensdag': 2,
    u'donderdag': 3,
    u'vrijdag': 4,
    u'zaterdag': 5,
    u'zondag': 6,
}

SHORT_WEEKDAYS = {

}

MONTHS = {
    u'januari': 1,
    u'februari': 2,
    u'maart': 3,
    u'april': 4,
    u'mei': 5,
    u'juni': 6,
    u'juli': 7,
    u'augustus': 8,
    u'september': 9,
    u'oktober': 10,
    u'november': 11,
    u'december': 12,
}

SHORT_MONTHS = {

}

TRANSLATIONS = {
    'nl_NL': {
        'today': u"vandaag",
        'today_abbrev': u"vandaag",
        'tomorrow': u'morgen',
        'this': u'deze',
        'midnight': u'middernacht',
        'every day': u'elke dag',
        'the': u'het',
        'and': u'en',
        'at': u'om',
        'except': u'behalve',
        'from_day': u'van',
        'to_day': u'tot',
        'from_hour': u'van',
        'to_hour': u'tot',
    },
}

########################################################
# Patterns and keywords only used for language detection
# (note: some could be used for date parsing)
########################################################
DATE_PATTERNS = {
    u'XX/XX/XXXX',
    u'XX-XX-XXXX',
    u'XX.XX.XXXX',
}

ADDITIONAL_KEYWORDS = {

}
