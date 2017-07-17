# -*- coding: utf-8 -*-

"""Spannish temporal data: weekday names, month names, etc."""

WEEKDAYS = {
    u'lunes': 0,
    u'martes': 1,
    u'miércoles': 2,
    u'miercoles': 2,
    u'jueves': 3,
    u'viernes': 4,
    u'sábado': 5,
    u'sabado': 5,
    u'domingo': 6,
}

SHORT_WEEKDAYS = {

}

MONTHS = {
    u'enero': 1,
    u'febrero': 2,
    u'marzo': 3,
    u'abril': 4,
    u'mayo': 5,
    u'junio': 6,
    u'julio': 7,
    u'agosto': 8,
    u'septiembre': 9,
    u'octubre': 10,
    u'noviembre': 11,
    u'diciembre': 12,
}

SHORT_MONTHS = {

}

TRANSLATIONS = {
    'es_ES': {
        'today': u"hoy",
        'today_abbrev': u"hoy",
        'tomorrow': u'mañana',
        'this': u'este',
        'midnight': u'medianoche',
        'every day': u'todos las dias',
        'the': u'el',
        'and': u'y',
        'at': u'a las',
        'except': u'excepto',
        'from_day': u'de',
        'to_day': u'a',
        'from_hour': u'de',
        'to_hour': u'a',
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
