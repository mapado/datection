# datection

Detect and normalize textual temporal expressions.

Example:
```python
# Detection of a simple time expression
>>> from datection import parse
>>> t = parse('15h30', 'fr')[0]
>>> t
<datection.serialize.TimeInterval at 0x2412610>
>>> t.to_python()
datetime.time(15, 30)
```

# Detection of a datetime
>>> dt = parse('le lundi 15 mars 2013 de 15h30 à 17h', 'fr')[0]
>>> dt
<datection.serialize.DateTime at 0x2412a10>
>>> dt.to_python()
(datetime.datetime(2013, 3, 15, 15, 30), datetime.datetime(2013, 3, 15, 17, 0))
```

## What time expressions are supported?

``datection`` supports the following temporal expressions:

* time (ex: 15h30)
* time intervals (ex: 15h30 - 17h)
* date (ex: mardi 16 mars 2013)
* date list (ex: 15, 16 et 17 mars 2012)
* date interval (ex: du 17 au 18 mars 2012)
* datetime (ex: le mercredi 18 janvier 2013 à 16h)
* datetime list (ex: le 6, 7, 8 avril 2015, de 16h à 17h)
* datetime interval (ex: du 17 au 19 avril 2012, de 17h à 21h)

## How does it work?

### Probing
The input text, passed to the ``datection.parse`` function is first probed for temporal markers.
If no weekday, month name, year or numeric date could be found, the parsing stops there and returns an empty list.

Examples:
```python
>>> from datection import probe
>>> probe('Hello world')  # no temporal markers
[]
>>> p = probe("En 2013, j'ai mangé une pomme, et elle était super bonne bonne bonne, comme le jour", 'fr')
>>> p
["En 2013, j'ai mangé une pomme, et el"]  # context of "2013"
```
If some temporal markers could be found, we extract the context around each of these markers.

####Note
If some of the returned Contexts overlap each other, they are automatically merged together, in a single context.
```python
>>> p = probe("Le 7 septembre 2013, j'ai mangé une pomme, et elle était super bonne", "fr")
>>> p
["Le 7 septembre 2013, j'ai mang\xc3\xa9 une pomme, et el"] # merged context of "septembre" and "2013"
```

### Normalizing
Each string context is then submitted to a battery of regexes, each of them tailored to detect a variety of temporal markers.
The result of the regex detection is them fed to a timepoint factory, which returns a Python object, subclassing the ``datection.serialize.Timepoint`` class.

It is highly possible that some result overlap others. For example, parsing the string "lundi 15 mars 2013 à 15h30" will yield 3 different results:

* lundi 15 mars 2013 → ``Date``
* 15h30 → ``TimeInterval``
* lundi 15 mars 2013 à 15h30 → ``DateTime``

The function ``datection._remove_subsets`` (poor name choice, will have to fix that someday) will return only the non overlapping, independant results.
In this example, it would only return the ``DateTime`` instance.


## Serializing
Each ``Timepoint`` subclass is provided with two serialization methods:

* ``to_python``: exports the object to standard Python format (``time``, ``date`` or ``datetime``)
* ``to_db``:  exports the object to a database compliant format, only based on datetime intervals

### Serialization conversion table
Expression | Timepoint | to_python | to_db
--- | --- | --- | ---
le 5 janvier 2013 | Date | datetime.date(2013, 1, 5) | [(datetime.datetime(2013, 1, 5, 0, 0),<br><br> datetime.datetime(2013, 1, 5, 23, 59, 59))]
Le 5 et 6 janvier 2013 | DateList | [datetime.date(2013, 1, 15),<br> datetime.date(2013, 1, 16)]` |[(datetime.datetime(2013, 1, 15, 0, 0),<br> datetime.datetime(2013, 1, 15, 23, 59, 59)),<br>(datetime.datetime(2013, 1, 16, 0, 0),<br>datetime.datetime(2013, 1, 16, 23, 59, 59))]
du 5 au 10 juillet 2013 | DateInterval | [datetime.date(2013, 7, 5),<br> datetime.date(2013, 7, 10)] | [(datetime.datetime(2013, 7, 5, 0, 0),<br> datetime.datetime(2013, 7, 10, 23, 59, 59))]
15h30 | TimeInterval | datetime.time(15, 30) | None
de 15h30 à 16h | TimeInterval | (datetime.time(15, 30),<br> datetime.time(16, 0)) | None
le 18 janvier 2013 à 16h | DateTime | datetime.datetime(2013, 1, 18, 16, 0) | [(datetime.datetime(2013, 1, 18, 16, 0),<br> datetime.datetime(2013, 1, 18, 16, 0))]
le 6 et 8 avril 2015, de 16h à 17h | DateTimeList | [(datetime.datetime(2015, 4, 6, 16, 0),<br> datetime.datetime(2015, 4, 6, 17, 0)),<br>(datetime.datetime(2015, 4, 8, 16, 0),<br> datetime.datetime(2015, 4, 8, 17, 0))] | [(datetime.datetime(2015, 4, 6, 16, 0),<br> datetime.datetime(2015, 4, 6, 17, 0)),<br>(datetime.datetime(2015, 4, 8, 16, 0),<br> datetime.datetime(2015, 4, 8, 17, 0))]
du 17 au 18 avril 2012, de 17h à 21h | DateTimeInterval | [(datetime.datetime(2012, 4, 17, 17, 0),<br> datetime.datetime(2012, 4, 17, 21, 0)),<br>(datetime.datetime(2012, 4, 18, 17, 0),<br>datetime.datetime(2012, 4, 18, 21, 0))] | [(datetime.datetime(2012, 4, 17, 17, 0) datetime.datetime(2012, 4, 17, 21, 0)),<br> (datetime.datetime(2012, 4, 18, 17, 0),<br> datetime.datetime(2012, 4, 18, 21, 0))]

## Pitfalls

For now, only French is supported, but porting to another language merely consists in translating the regexes from one language to another.

Also, recurrence expressions (all wednesdays, etc) are not yet supported.
