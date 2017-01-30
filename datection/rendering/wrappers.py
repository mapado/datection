# -*- coding: utf-8 -*-
import re
from functools import wraps


def postprocess(strip=True, trim_whitespaces=True, lstrip_pattern=None,
                capitalize=False, rstrip_pattern=None):
    """Post processing text formatter decorator."""
    def wrapped_f(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            text = func(*args, **kwargs)
            text = text.replace(', ,', ', ')
            if trim_whitespaces:
                text = re.sub(r'\s+', ' ', text)
            if lstrip_pattern:
                text = text.lstrip(lstrip_pattern)
            if rstrip_pattern:
                text = text.rstrip(rstrip_pattern)
            if strip:
                text = text.strip()
            if capitalize:
                text = text.capitalize()
            return text
        return wrapper
    return wrapped_f


def cached_property(f):
    """Lazy loading decorator for object properties"""
    attr_name = '_' + f.__name__

    @property
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, f(self))
        return getattr(self, attr_name)
    return wrapper
