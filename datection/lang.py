# -*- coding: utf-8 -*-

"""
Definition of default locales for given languages
"""

import re


DEFAULT_LOCALES = {
    'fr': 'fr_FR.UTF8',
    'en': 'en_US.UTF8',
}


def getlocale(lang):
    if lang in DEFAULT_LOCALES:
        return DEFAULT_LOCALES[lang]


def detect_language(text, lang):
    """ Language check to detect locale """
    if re.search(r' (am|pm) ', text):
        return 'en'

    return lang
