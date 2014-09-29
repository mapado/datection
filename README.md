# datection
Multilingual library for normalisation and rendering of temporal expressions.

## How to use it?

### Normalisation
The normalisation step extracts temporal expressions from a text, using a language specific grammar, and exports them into a short, storable format.

#### Example

```python
>>> import datection

>>> from datetime import datetime

# simple datetime
>>> datection.export(u"Le 4 mars 2015 à 18h30", "fr")
[{'duration': 0,
  'rrule': 'DTSTART:20150304\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=30;BYHOUR=18',
  'span': (0, 23)}]

# date interval with a recurrent exclusion
>>> datection.export(u"Du 5 au 29 mars 2015, sauf le lundi", "fr")
[{'duration': 1439,
  'excluded': ['DTSTART:20150305\nRRULE:FREQ=DAILY;BYDAY=MO;BYHOUR=0;BYMINUTE=0;UNTIL=20150329T000000'],
  'rrule': 'DTSTART:20150305\nRRULE:FREQ=DAILY;BYHOUR=0;BYMINUTE=0;INTERVAL=1;UNTIL=20150329',
  'span': (0, 36)}]

# yearless date, with argument date reference
>>> datection.export(u"Le 4 mars à 18h30", "fr", reference=datetime(2015, 1, 1))
[{'duration': 0,
  'rrule': 'DTSTART:20150304\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=30;BYHOUR=18',
  'span': (0, 18)}]

# past datetime
>>> datection.export(u"Le 4 mars 1990 à 18h30", "fr")
[]

# past datetime and authorized past exports
>>> datection.export(u"Le 4 mars 1990 à 18h30", "fr", only_future=False)
[{'duration': 0,
  'rrule': 'DTSTART:19900304\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=30;BYHOUR=18',
  'span': (0, 18)}]

# continuous datetime interval
>>> datection.export(u"Du 5 avril à 22h au 6 avril 2015 à 8h", "fr")
[{'continuous': True,
  'duration': 600,
  'rrule': 'DTSTART:20150405\nRRULE:FREQ=DAILY;BYHOUR=22;BYMINUTE=0;INTERVAL=1;UNTIL=20150406T235959',
  'span': (0, 38)}]

```

#### Export format

The export format contains 6 different items:

* ``rrule``: a parseable expression, generating all the datetimes described by the expression. See the [python-dateutil](http://labix.org/python-dateutil) documentation and [RFC 2445](http://www.ietf.org/rfc/rfc2445.txt) for more details
* ``duration``: the duration (in minutes) between each start datetime, egenrated by the rrule, and its end counterpart:

  - 8h → 9h: duration = 60
  - at 8pm: duration = 0
  - all day: duration = 1439

* ``span``: the character interval defining where the temporal expression was found in the text
* ``continuous``: boolean flag, indicating if the time interval is continuous or not.
* ``excluded``: a list of rrules exclusion rrules.
* ``unlimited``: if True, the rrules are considered as infinite.

### Rendering

The rendering step renders the export format in human readable formats, in a specific language.

Several formats can be chosen from:

 * default
 * short: shorter than the default output, omits some information when possible (the year, for example), and contextualize the result
 * place: display the export as opening hours
 * SEO: synthetic information, only displaying the month and the year. Used for SEO purposes.

```python
>>> import datection
>>> schedule = datection.export(u"Le 5 mars 2015, 15h30 - 16h", "fr")

# default
>>> datection.display(schedule, 'fr')
u'Le 5 mars 2015 de 15 h 30 à 16 h'

# short
>>> datection.display(schedule, 'fr', short=True)
u'Le 5 mars de 15 h 30 à 16 h'
>>> datection.display(schedule, 'fr', short=True, reference=date(2015, 3, 3))
u'Ce jeudi de 15 h 30 à 16 h'
>>> datection.display(schedule, 'fr', short=True, reference=date(2015, 3, 4))
u'Demain de 15 h 30 à 16 h'
>>> datection.display(schedule, 'fr', short=True, reference=date(2015, 3, 5))
u"Aujourd'hui de 15 h 30 ç 16 h"

# SEO
>>> datection.display(schedule, 'fr', seo=True)
u'mars 2015'

# opening hours / place
>>> schedule = datection.export(u"Du lundi au vendredi de 8h à 12h30 et de 14h à 19h30", "fr")
>>> datection.display(schedule, 'fr', place=True)
u"""Lundi de 8 h à 12 h 30 et de 14 h à 19 h 30
Mardi de 8 h à 12 h 30 et de 14 h à 19 h 30
Mercredi de 8 h à 12 h 30 et de 14 h à 19 h 30
Jeudi de 8 h à 12 h 30 et de 14 h à 19 h 30
Vendredi de 8 h à 12 h 30 et de 14 h à 19 h 30
"""
```
