"""
Definition of default locales for given languages
"""

DEFAULT_LOCALES = {
    'fr': 'fr_FR.UTF8',
    'en': 'en_US.UTF8'
}


def getlocale(lang):
    if lang in DEFAULT_LOCALES:
        return DEFAULT_LOCALES[lang]
