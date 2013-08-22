## How to work with translations and gettext?

First, read [that](http://pymotw.com/2//gettext/index.html) and/or [that](http://wiki.laptop.org/go/Python_i18n).
Now that you're done reading it, you should know the difference between `.pot`, `po` and `mo` files.
If not, here's a quick summary, I'm feeling light-hearted:

 * `pot`: gettext Portable Object Template. Contains the layout of all the `.po` files
 * `po`: gettext Portable Object. Contains the boilerplate defined in the `pot` file, plus actual translations and language information
 * `mo`: gettext Machine Object. Compiled translations usable by gettext.

## Create the `pot` file for the first time

Use the following command to generate the `pot` file.

```bash
$ find ../datection -type f -iname "*.py" | xgettext -f - --output datection.pot
```

Complete the version, copyright, email, etc, information.

## Generate the `po` files
```bash
$ cp datection.pot language/LC_MESSAGES/datection.po
```

**Note**: Each `po` file must be located in a `language`/LC\_MESSAGES directory. By convention, we name our `language` directories as `language`_`country_code`.

Examples:

* fr_FR
* en_US

Then, complete each `po` file by adding the translations.

## Generate the `mo` files
```bash
for pofile in `find . -type f -iname "*.po"`;
do
    msgfmt  $pofile --output `echo $pofile | cut -d. -f-2`.mo;
done
```

## Update the `po` files
Each `po` file contains the line in which the translation is located. If your source code evolves, you need to re-generate the files so that they mirror the last state of the code.

TO do that, you can use this script:

```bash
for pofile in `find . -type f -iname "*.po"`;
do
    echo '' > messages.po;
    find ../datection -type f -iname "*.py" | xgettext -j -f -;
    msgmerge -N $pofile messages.po > $pofile;
    rm messages.po;
done
```
```
