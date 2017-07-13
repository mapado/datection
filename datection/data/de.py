# -*- coding: utf-8 -*-

"""German temporal data: weekday names, month names, etc."""

WEEKDAYS = {
    u'montag': 0,
    u'dienstag': 1,
    u'mittwoch': 2,
    u'donnerstag': 3,
    u'freitag': 4,
    u'samstag': 5,
    u'sonntag': 6,
}

SHORT_WEEKDAYS = {

}

MONTHS = {
    u'januar': 1,
    u'februar': 2,
    u'märz': 3,
    u'marz': 3,
    u'april': 4,
    u'mai': 5,
    u'juni': 6,
    u'juli': 7,
    u'august': 8,
    u'september': 9,
    u'oktober': 10,
    u'november': 11,
    u'dezember': 12,
}

SHORT_MONTHS = {

}

TRANSLATIONS = {
    'de_DE': {
        'today': u"heute",
        'today_abbrev': u"heute",
        'tomorrow': u'morgen',
        'this': u'dies',
        'midnight': u'mitternacht',
        'every day': u'täglich',
        'the': u'am',
        'and': u'und',
        'at': u'um',
        'except': u'nur',
        'from_day': u'von',
        'to_day': u'bis',
        'from_hour': u'von',
        'to_hour': u'bis',
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
