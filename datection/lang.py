# -*- coding: utf-8 -*-

"""
Definition of default locales for given languages
"""
from __future__ import division

from past.utils import old_div
import re
import operator

DEFAULT_LOCALES = {
    'fr': 'fr_FR.UTF8',
    'en': 'en_US.UTF8',
}


RENDERING_LOCALES = {
    'fr': 'fr_FR.UTF8',
    'en': 'en_US.UTF8',
    'de': 'de_DE.UTF8',
    'es': 'es_ES.UTF8',
    'it': 'it_IT.UTF8',
    'nl': 'nl_NL.UTF8',
    'pt': 'pt_BR.UTF8',
    'ru': 'ru_RU.UTF8',
}


WORD_DICTS = ['WEEKDAYS', 'SHORT_WEEKDAYS', 'MONTHS', 'SHORT_MONTHS']
WORD_LISTS = ['DATE_PATTERNS', 'ADDITIONAL_KEYWORDS']

# Global dictionnary containing date keywords for each language
# It is filled at the first call of get_lang_keywords()
LANG_KEYWORDS = {}


def getlocale(lang):
    if lang in RENDERING_LOCALES:
        return RENDERING_LOCALES[lang]


def detect_language(text, lang):
    """
    Language check to detect locale

    @param text(string): string containing the date
    @param lang(string): a-priori language (e.g: from activity locale)

    @return: the most apropriate language to use for datection
    """
    proposed_lang, proba = light_lang_detection(text)

    # override a-priori language if we are confident of the
    # detection
    if lang in DEFAULT_LOCALES:
        if (proposed_lang != lang) and (proba > 0.5):
            return proposed_lang
    elif proba > 0:
        return proposed_lang

    return lang


def fill_lang_keywords_with_lang(lang):
    """
    Fills the global dictionnary LANG_KEYWORDS with the
    keywords for the given language. Keywords are taken from
    the module data/($lang).py

    @param lang(String): Language (fr/en/...)
    """
    # import module for the given lang
    import_list = WORD_DICTS + WORD_LISTS + ['TRANSLATIONS']
    module = __import__('datection.data.' + lang, fromlist=import_list)

    global LANG_KEYWORDS

    for word_dict in WORD_DICTS:
        if hasattr(module, word_dict):
            words = list(getattr(module, word_dict).keys())
            for word in words:
                LANG_KEYWORDS.setdefault(word, set()).add(lang)

    if hasattr(module, 'TRANSLATIONS'):
        translations = getattr(module, 'TRANSLATIONS')
        for locale in list(translations.keys()):
            for expr in list(translations[locale].values()):
                for word in expr.split(' '):
                    LANG_KEYWORDS.setdefault(word, set()).add(lang)

    for word_list in WORD_LISTS:
        if hasattr(module, word_list):
            date_patterns = getattr(module, word_list)
            for pattern in date_patterns:
                LANG_KEYWORDS.setdefault(pattern, set()).add(lang)


def build_lang_keywords():
    """
    Builds the global dictionnary LANG_KEYWORDS with
    all keywords defined in data folder (for the languages defined
    in DEFAULT_LOCALES)
    """
    for lang in DEFAULT_LOCALES:
        fill_lang_keywords_with_lang(lang)


def get_lang_keywords():
    """
    Returns the global LANG_KEYWORDS containing the keywords
    for each languages. LANG_KEYWORDS will be re-computed if
    empty.
    """
    if len(LANG_KEYWORDS) == 0:
        build_lang_keywords()

    return LANG_KEYWORDS


def light_tokenize(text):
    """
    Performs simple tokenization on the input text.

    @param text(String): raw date text

    @return: first 10 tokens of the input text
    """
    # remove punctuation (but keep '/' and '.' for dates and abbreviations)
    chars_to_remove = ['!', '?', '>', '=', ';', ':']
    rx = '[%s]' % re.escape(''.join(chars_to_remove))
    text_no_punct = re.sub(rx, ' ', text).lower()

    # flatten numbers to detect date patterns (e.g YYYY/DD/MM)
    text_flat_num = re.sub('\d', 'X', text_no_punct)

    text_tokens = [tok for tok in text_flat_num.split(' ') if (tok != '')]
    return text_tokens[:10]


def light_lang_detection(text):
    """
    Performs a lang detection without doing a complex parsing. Input text
    is scored against keywords specific to the available languages.

    @param text(String): raw date text

    @return: best language candidate and its score
    """
    text_tokens = light_tokenize(text)

    lang_keywords = get_lang_keywords()

    matching_tokens = [tok for tok in text_tokens if tok in list(lang_keywords.keys())]

    # contains score for each language (default 0)
    lang_scores = dict.fromkeys(list(DEFAULT_LOCALES.keys()), 0)

    for token in matching_tokens:
        for lang in lang_keywords[token]:
            # division by len(lang_keywords[token]) because word shared
            # by many languages should have a low impact on the score
            lang_scores[lang] += old_div(1., len(lang_keywords[token]))

    # compute proba for the best candidate (no need for softmax (small range))
    best_lang = max(list(lang_scores.items()), key=operator.itemgetter(1))[0]
    sum_scores = float(sum(lang_scores.values()))
    proba = (old_div(lang_scores[best_lang], sum_scores)) if (sum_scores != 0.) else 0

    return best_lang, proba
