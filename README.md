# datection

Detect, serialize and deserialize temporal expressions.

Example:
```python
# Detection of a simple time expression
>>> from datection import parse
>>> t = parse('15h30', 'fr')[0]
>>> t
<datection.serialize.TimeInterval at 0x2412610>
>>> t.serialize()
{'end_time': None,
'start_time': {'hour': 15, 'minute': 30},
'timepoint': 'time_interval',
'valid': True}

# Detection of a datetime
>>> dt = parse('le lundi 15 mars 2013 de 15h30 à 17h', 'fr')[0]
>>> dt
<datection.serialize.DateTime at 0x2412a10>
>>> dt.serialize()
{'date': {'day': 15, 'month': 3, 'year': 2013},
'time': {'end_time': {'hour': 17, 'minute': 0},
'start_time': {'hour': 15, 'minute': 30}},
'timepoint': 'datetime',
'valid': True}
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
>>> from datection.context import probe
>>> probe('Hello world')  # no temporal markers
[]
>>> p = probe("Le lundi 5 mars 2013, j'ai mangé une pomme, et elle était super bonne bonne bonne, comme le jour", 'fr')
>>> p
[Le lundi 5 mars 2013, j'ai mangé une pomme, et elle était super,  # context of 'lundi'
Le lundi 5 mars 2013, j'ai mangé une pomme, et elle était super bonn,  # context of 'mars'
Le lundi 5 mars 2013, j'ai mangé une pomme, et elle étai]  # context of '2013'
>>> type(p[0])
datection.context.Context
```

If some temporal markers could be found, we extract the context around each of these markers.
If some of the returned Contexts overlap each other, we merge them.

Example:
```python
>>> from datection.context import independants
>>> independants(probe("Le lundi 5 mars 2013, j'ai mangé une pomme, et elle était super bonne bonne bonne, comme le jour", 'fr'))
["Le lundi 5 mars 2013, j'ai mang\xc3\xa9 une pomme, et elle \xc3\xa9tait super bonn"]
```

### Serializing
Each ``Context`` object is then submitted to a battery of regexes, each of them tailored to detect a variety of temporal markers.
The result of the regex detection is them fed to a timepoint factory, which returns a Python object, with notably two serialization methods:

* ``serialize``: exports the object to the JSON format
* ``to_sql``: exports the object to standard Python format (``datetime``) in order to insert it into an SQL database

Example
```python
>>> from datection import parse
>>> dt = parse('lundi 15 mars 2013, de 5h à 8h30')
>>> dt.serialize()
{'date': {'day': 15, 'month': 3, 'year': 2013},
'time': {'end_time': {'hour': 8, 'minute': 30},
'start_time': {'hour': 5, 'minute': 0}},
'timepoint': 'datetime',
'valid': True}
>>> dt.to_sql()
(datetime.datetime(2013, 3, 15, 5, 0), datetime.datetime(2013, 3, 15, 8, 30))
```

### Deserializing
The JSON-serialized format can be deserialized, to recreate a Python datection object.

To do so, use the ``datection.deserialize`` module:
```python
>>> from datection.deserialize import deserialize
>>> ser = dt.serialize()
>>> newdt = deserialize(ser)
>>> dt == newdt
True
```

## Pitfalls

For now, only French is supported, but porting to another language merely consists in translating the regexes from one language to another.

Also, recurrence expressions (all wednesdays, etc) are not yet supported.
