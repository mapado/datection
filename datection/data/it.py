# -*- coding: utf-8 -*-

"""Italian temporal data: weekday names, month names, etc."""

WEEKDAYS = {
    u'Lunedì': 0,
    u'Lunedi': 0,
    u'Martedì': 1,
    u'Martedi': 1,
    u'Mercoledì': 2,
    u'Mercoledi': 2,
    u'Giovedì': 3,
    u'Giovedi': 3,
    u'Venerdì': 4,
    u'Venerdi': 4,
    u'sabato': 5,
    u'domenica': 6,
}

SHORT_WEEKDAYS = {

}

MONTHS = {
    u'gennaio': 1,
    u'febbrario': 2,
    u'marzo': 3,
    u'aprile': 4,
    u'mag': 5,
    u'giugno': 6,
    u'luglio': 7,
    u'agosto': 8,
    u'settembre': 9,
    u'ottobre': 10,
    u'novembre': 11,
    u'dicembre': 12,
}

SHORT_MONTHS = {

}

TRANSLATIONS = {
    'it_IT': {
        'today': u"oggi",
        'today_abbrev': u"oggi",
        'tomorrow': u'domani',
        'this': u'questo',
        'midnight': u'mezzanotte',
        'every day': u'ogni giorno',
        'the': u'il',
        'and': u'e',
        'at': u'alle',
        'except': u'eccetto',
        'from_day': u'da',
        'to_day': u'a',
        'from_hour': u'dalle',
        'to_hour': u'alle',
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
