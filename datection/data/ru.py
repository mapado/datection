# -*- coding: utf-8 -*-

"""Russian temporal data: weekday names, month names, etc."""

WEEKDAYS = {
    u'Понедельник': 0,
    u'Вторник': 1,
    u'Среда': 2,
    u'Четверг': 3,
    u'Пятница': 4,
    u'Суббота': 5,
    u'Воскресенье': 6,
}

SHORT_WEEKDAYS = {

}

MONTHS = {
    u'Январь': 1,
    u'Февраль': 2,
    u'Март': 3,
    u'Апрель': 4,
    u'Май': 5,
    u'Июнь': 6,
    u'Июль': 7,
    u'Август': 8,
    u'Сентябрь': 9,
    u'Октябрь': 10,
    u'Ноябрь': 11,
    u'Декабрь': 12,
}

SHORT_MONTHS = {

}

TRANSLATIONS = {
    'ru_RU': {
        'today': u"сегодня",
        'today_abbrev': u"сегодня",
        'tomorrow': u'завтра',
        'this': u'этот',
        'midnight': u'полночь',
        'every day': u'Ежедневно',
        'the': u'на',
        'and': u'и',
        'at': u'в',
        'except': u'кроме',
        'from_day': u'c',
        'to_day': u'по',
        'from_hour': u'c',
        'to_hour': u'до',
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
