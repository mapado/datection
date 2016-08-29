# -*- coding: utf-8 -*-

"""French temporal data: weekday names, month names, etc."""

WEEKDAYS = {
    u'lundi': 0,
    u'mardi': 1,
    u'mercredi': 2,
    u'jeudi': 3,
    u'vendredi': 4,
    u'samedi': 5,
    u'dimanche': 6,
}

SHORT_WEEKDAYS = {
    u'lun': 0,
    u'mar': 1,
    u'mer': 2,
    u'merc': 2,
    u'mercr': 2,
    u'jeu': 3,
    u'ven': 4,
    u'sam': 5,
    u'dim': 6,
}

MONTHS = {
    u'janvier': 1,
    u'février': 2,
    u'fevrier': 2,
    u'mars': 3,
    u'avril': 4,
    u'mai': 5,
    u'juin': 6,
    u'juillet': 7,
    u'août': 8,
    u'aout': 8,
    u'septembre': 9,
    u'octobre': 10,
    u'novembre': 11,
    u'décembre': 12,
    u'decembre': 12,
}

SHORT_MONTHS = {
    u'jan': 1,
    u'janv': 1,
    u'fév': 2,
    u'févr': 2,
    u'fev': 2,
    u'fevr': 2,
    u'mar': 3,
    u'avr': 4,
    u'juil': 7,
    u'juill': 7,
    u'sep': 9,
    u'sept': 9,
    u'oct': 10,
    u'nov': 11,
    u'dec': 12,
    u'déc': 12,
}

TRANSLATIONS = {
    'fr_FR': {
        'today': u"aujourd'hui",
        'today_abbrev': u"auj.",
        'tomorrow': u'demain',
        'this': u'ce',
        'midnight': u'minuit',
        'every day': u'tous les jours',
        'the': u'le',
        'and': u'et',
        'at': u'à',
        'except': u'sauf',
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
    u'matin',
    u'journée',
    u'soirée',
    u'de',
    u'du',
    u'entre',
}
