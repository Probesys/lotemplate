# OOTemplateFiller

OOTemplateFiller is a script that fills a given document, used as a template, with elements given in a 
json file. This script can be used as an API (using Flask), a CLI or a python module for your own code.
For more information on a specific usage, read, the `Execute and use the API` or 
`Execute and use the CLI` section.

## Functionalities
- scans the template to extract the variables sheet
- search for all possible errors before filling
- filling the template
- export the template

## Requirements
- LibreOffice (the console-line version will be enough)
- a Java JRE
- the package `libreoffice-java-common`
- some python packages specified in [requirement.txt](requirements.txt) that you can install with
  `pip install -r requirements.txt`. `Flask` is optional, as it is used only for the API, as well
  as `configargparse`, used only for the CLI.

more informations on [the github page of unotools](https://github.com/t2y/unotools)

## Execute and use the API

Run the following command on your terminal or a server
```shell
soffice "--accept=socket,host=[HOST],port=[PORT];urp;StarOffice.ServiceManager"
```

with the host and port you wish (recommended = localhost:2002). Be sure that they correspond to the ones provided in the
[config.ini](config.ini) file 

Then run the following command on the same server, or another one

```shell
python3 -m flask run
```

## Execute and use the CLI

Run the following command on your terminal or a server
```shell
soffice "--accept=socket,host=[HOST],port=[PORT];urp;StarOffice.ServiceManager"
```

with the host and port you wish (recommended = localhost:2002). Be sure that they correspond to the ones provided in the
[config.ini](config.ini) file , or to the one provided via command-line

Then run the script with the following arguments :
```
usage: ootemplate.py [-h] [--json_file JSON_FILE [JSON_FILE ...]]
                     [--json JSON [JSON ...]] [--output OUTPUT] [--config CONFIG]
                     --host HOST --port PORT [--scan] [--force_replacement]
                     template_file

positional arguments:
  template_file         Template file to scan or fill

optional arguments:
  -h, --help            show this help message and exit
  --json_file JSON_FILE [JSON_FILE ...], -jf JSON_FILE [JSON_FILE ...]
                        Json file(s) that must fill the template, if any
  --json JSON [JSON ...], -j JSON [JSON ...]
                        Json strings that must fill the template, if any
  --output OUTPUT, -o OUTPUT
                        Name of the filled file, if the template should be
                        filled. supported formats: pdf, html, docx, png, odt
  --config CONFIG, -c CONFIG
                        Configuration file path
  --host HOST           Host address to use for the libreoffice connection
  --port PORT           Port to use for the libreoffice connexion
  --scan, -s            Specify if the program should just scan the template
                        and return the information, or fill it.
  --force_replacement, -f
                        Specify if the program should ignore the scan's result
```
Args that start with '--' (eg. --json) can also be set in a config file
(config.ini or specified via --config). Config file syntax allows: key=value,
flag=true, stuff=[a,b,c] (for details, [see syntax](https://goo.gl/R74nmi)).
If an arg is specified in more than one place, then commandline values
override config file values which override defaults.

All the specified files can be local or network-based.

Get a file to fill with the `--scan` argument, and fill the fields you want. Add elements to the list
of an array to dynamically add rows. Then pass the file, and the completed json file(s) (using `--json_file`)
to fill it.

## Template Syntax
- text variables : putting '$variable' in the document is enough to add the variable 'variable'.
- image variables : add any image in the document, and put in the name of the image (properties) '$' followed by
  the desired name ('$image' for example to add the image 'image')
- dynamic arrays : allows you to add an unknown number of rows to the array.
  the array, but only on the last line. in the same way as for images, name your array variable
  with a '$' in front of it.

## Supported formats

### Import
| Format                  | ODT, OTT | DOC, DOCX | HTML | RTF | TXT | OTHER |
|-------------------------|----------|-----------|------|-----|-----|-------|
| text variables support  | ✅        | ✅         | ✅    | ✅   | ✅   | ❌     |
| image variables support | ✅        | ✅         | ✅    | ❌   | ❌   | ❌     |
| dynamic tables support  | ✅        | ❌         | ❌    | ❌   | ❌   | ❌     |
### Export
odt, pdf, html, docx.

Other formats can be easily added by adding the format information in the dictionary `formats` in 
[ootemplate/\_\_init__.py](ootemplate/__init__.py) > Template > export().

Format information can be found on the 
[unoconv repo](https://github.com/unoconv/unoconv/blob/94161ec11ef583418a829fca188c3a878567ed84/unoconv#L391).

## Unsolvable problems

The error `UnoBridgeException` happens frequently and 
unpredictably, and this error stops the soffice processus. This error, particularly annoying, is unfortunately 
impossible to fix, since it's a pyUNO - or soffice - bug, unresolved since 2015. It is therefore very unlikely that 
this bug will ever be fixed.
Here is a non-exhaustive list of cases that can cause this bug :
- The `.~lock.[FILENAME].odt#` file is present in the folder where the document is open.  This file is created when the 
  file is currently edited via libreoffice or openoffice, and deleted when the programs in which it is edited are 
  closed.
- The first line of the document is occupied by a table (juste jump a line, it will solve the problem)
- The background of document is an image, and is overlayed by many textfields

The amount of memory used by soffice can increase with its use, even when open files are properly closed (which is the 
case). Again, this is a bug in OpenOffice/soffice that has existed for years.

For trying to fix these problems, you can try:
- Use the most recent stable release of LibreOffice (less memory, more stable, fewer crashes)
- Use the native LibreOffice python binary to run this script

## Useful links
- [JODConverter wiki for list formats compatibles with LibreOffice](https://github.com/sbraconnier/jodconverter/wiki/Getting-Started)
- [The unoconv source code, written in python with PyUNO](https://github.com/unoconv/unoconv/blob/master/unoconv)
- [Unoconv source code for list formats - and properties - compatible with LibreOffice for export](https://github.com/unoconv/unoconv/blob/94161ec11ef583418a829fca188c3a878567ed84/unoconv#L391)
- [OpenOffice Python Bridge informations and code exemples](http://www.openoffice.org/udk/python/python-bridge.html)
- [com.sun.star Java API docs (On which pyuno is based - but is not identical)](https://www.openoffice.org/api/docs/common/ref/com/sun/star/module-ix.html)
- [Old OOTemplate code](https://gitlab.probesys.com/troizaire/ootemplate/-/blob/c8f1e759db9494823fa4dded8c70a31d4e047c05/old.py)

## To do
1. faire du CLI une API REST basée sur le même noyau avec flask
   - [se renseigner sur Flask](https://flask.palletsprojects.com/en/2.0.x/)
   - faire une route pour upload un template et qui renvoie le json du scan
   - faire une route pour delete un template
   - faire une route qui delete est recréée (modif)
   - faire une route pour remplir et renvoyer le document rempli
2. implémenter l'API sur nemoweb
   - [se renseigner sur Ruby on Rails](https://www.eduonix.com/new_dashboard/Learn-Ruby-on-Rails-By-Building-Projects)
    
## To consider

- la possibilitée de noter les variables de tableaux d'une autre manière (ex : '&') pour pouvoir placer
des variables statiques et des variables de tableau dynamiques, demander son avis à cyril dès son retour
- la possibilitée d'avoir des images dans les tableaux dynamiques
