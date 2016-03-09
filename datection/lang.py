# -*- coding: utf-8 -*-

"""
Definition of default locales for given languages
"""

import re
from datection.tokenize import Tokenizer


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

    if lang not in DEFAULT_LOCALES:
        tok_len_lang, proposed_lang = max(
            (len(Tokenizer(text, key).tokenize()), key)
            for key in DEFAULT_LOCALES.keys()
        )

        if tok_len_lang:
            lang = proposed_lang

    return lang
