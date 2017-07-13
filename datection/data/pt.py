# -*- coding: utf-8 -*-

"""Portugese temporal data: weekday names, month names, etc."""

WEEKDAYS = {
    u'segunda': 0,
    u'terça': 1,
    u'terca': 1,
    u'quarta': 2,
    u'quinta': 3,
    u'sexta': 4,
    u'sábado': 5,
    u'sabado': 5,
    u'domingo': 6,
}

SHORT_WEEKDAYS = {

}

MONTHS = {
    u'janeiro': 1,
    u'fevereiro': 2,
    u'março': 3,
    u'marco': 3,
    u'abril': 4,
    u'maio': 5,
    u'junho': 6,
    u'julho': 7,
    u'agosto': 8,
    u'setembro': 9,
    u'outubro': 10,
    u'novembro': 11,
    u'dezembro': 12,
}

SHORT_MONTHS = {

}

TRANSLATIONS = {
    'pt_BR': {
        'today': u"hoje",
        'today_abbrev': u"hoje",
        'tomorrow': u'amanhã',
        'this': u'isto',
        'midnight': u'meia-noite',
        'every day': u'a cada dia',
        'the': u'a',
        'and': u'e',
        'at': u'às',
        'except': u'salvo',
        'from_day': u'de',
        'to_day': u'a',
        'from_hour': u'das',
        'to_hour': u'às',
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
