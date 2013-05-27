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

##  Detection of a datetime
```python
>>> dt = parse('le lundi 15 mars 2013 de 15h30 à 17h', 'fr')[0]
>>> dt
<datection.serialize.DateTime at 0x2412a10>
>>> dt.to_python()
(datetime.datetime(2013, 3, 15, 15, 30), datetime.datetime(2013, 3, 15, 17, 0))
```

###  What time expressions are supported?

``datection`` supports the following temporal expressions:

* time (ex: 15h30)
* time intervals (ex: 15h30 - 17h)
* date (ex: mardi 16 mars 2013)
* date list (ex: 15, 16 et 17 mars 2012)
* date interval (ex: du 17 au 18 mars 2012)
* datetime (ex: le mercredi 18 janvier 2013 à 16h)
* datetime list (ex: le 6, 7, 8 avril 2015, de 16h à 17h)
* datetime interval (ex: du 17 au 19 avril 2012, de 17h à 21h)

###  How does it work?

####  Probing
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

#### Normalizing
Each string context is then submitted to a battery of regexes, each of them tailored to detect a variety of temporal markers.
The result of the regex detection is them fed to a timepoint factory, which returns a Python object, subclassing the ``datection.serialize.Timepoint`` class.

Each ``Timepoint`` subclass is provided with two normalization methods:

* ``to_python``: exports the object to standard Python format (``time``, ``date`` or ``datetime``)
* ``to_db``:  exports the object to a database compliant format, only based on ``datetime`` intervals

##### Note
It is highly possible that some result overlap others. For example, parsing the string "lundi 15 mars 2013 à 15h30" will yield 3 different results:

* lundi 15 mars 2013 → ``Date``
* 15h30 → ``TimeInterval``
* lundi 15 mars 2013 à 15h30 → ``DateTime``

The ``parse`` function automatically select the "largest" results, overlapping others, so you always get the most senseful results.

##### <a id="conv" name="conv"></a>Serialization conversion table

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

#####Note:
If the year is missing, the value of the current year is taken.

Examples:

* "5 octobre": 5/10/2013
* "du 5 au 8 juin": 5/06/2013 → 8/06/2013
* "le 5, 6, 7 et 13 novembre": 5/11/2013, 6/11/2013, 7/11/2013, 13/11/2013

## API

###``datection.parse``
Performs a date detection on text with all timepoint regex.

####Arguments

 * ``text``: text parsed for temporal expressions (``str`` or UTF-8 ``unicode``)
 * ``lang``: the 2 character code of the text language (``str``)
 * ``valid``: filter invalid results (`bool``, default to ``True``)

####Returns
A list of non overlapping normalized ``Timepoint`` objects.

####Example

```python
>>> parse("du 17 au 18 avril 2012, de 17h à 21h", "fr")
[<datection.normalize.DateTimeInterval at 0x31119d0>]
```

###``datection.probe``
Scans the text for very simple markers, indicating the presence of temporal patterns.

####Arguments
* ``text`` : the text to probe (type ``str`` or UTF-8 ``unicode``)
* ``lang``: the 2 character code of the text language (``str``)
* ``context_size``: the number of character before and after a probe
        match to be taken as context. (``int``, default to 50)

####Returns
A list of non overlapping text fragments, sorted by order of appearance in the input text.

####Example

```python
>>> text = u""" L'embarquement se fait 20 minutes avant.
La croisière démarre au pied de la Tour EIffel et dure 1h.
Réservation obligatoire au 01 76 64 14 68.
Promenade en famille
    La Croisière Enchantée
Dates et horaires
Du 6 octobre 2012 au 13 juillet 2013."""
>>> probe(text, "fr")
[' pied de la Tour EIffel et dure 1h.\nR\xc3\xa9servation obligatoire a',
 'roisi\xc3\xa8re Enchant\xc3\xa9e\nDates et horaires\nDu 6 octobre 2012 au 13 juillet 2013.']
```

### ``datection.to_python``
Performs a timepoint detection on text, and normalizes each result to python standard objects.

####Arguments
* ``text`` : the text to probe (type ``str`` or UTF-8 ``unicode``)
* ``lang``: the 2 character code of the text language (``str``)
* ``valid``: filter invalid results (`bool``, default to ``True``)


####Returns
A list of standard datetime python objects. [See the conversion table](#conv)

####Example

```python
>>> to_python('15 mars 2013', 'fr')
[datetime.date(2013, 3, 15)]
```

### ``datection.to_db``
Performs a timepoint detection on text, and normalizes each result to python standard objects,
in a format compliant to database insertion.

####Arguments
* ``text`` : the text to probe (type ``str`` or UTF-8 ``unicode``)
* ``lang``: the 2 character code of the text language (``str``)
* ``valid``: filter invalid results (`bool``, default to ``True``)


####Returns
A list of list of 2 tuples (start datetime, end datetime) [See the conversion table](#conv)

####Example

```python
>>> to_db('15 mars 2013', 'fr')
[[(datetime.datetime(2013, 3, 15, 0, 0),
   datetime.datetime(2013, 3, 15, 23, 59, 59))]]
```

### ``datection.to_mongo``

Performs a timepoint detection on text, and normalize each result to python standard objects,
in a format compliant to insertion into mongodb.

The format chages slightly from the result of the ``datection.to_db`` function, but the changes are purely cosmetic!

####Arguments
* ``text`` : the text to probe (type ``str`` or UTF-8 ``unicode``)
* ``lang``: the 2 character code of the text language (``str``)
* ``valid``: filter invalid results (`bool``, default to ``True``)


####Returns
A list of list of dict {'start' datetime, 'end' datetime}

####Example

```python
>>> to_mongo('15 mars 2013', 'fr')
[[{'end': datetime.datetime(2013, 3, 15, 23, 59, 59),
   'start': datetime.datetime(2013, 3, 15, 0, 0)}]]
```

### ``datection.is_future``
Assesses if the input datetime interval is located in the future.

####Arguments
* ``timepoint``: a 2-tuple composed of the start and end datetime
* ``reference``! the datetime used as a reference to the present. All datetimes after the reference are in the future.

####Returns
``True`` if the input timepoint is in the future. Else ``False``.


## Pitfalls

For now, only French is supported, but porting to another language merely consists in translating the regexes from one language to another.

Also, recurrence expressions (all wednesdays, etc) are not yet supported.
