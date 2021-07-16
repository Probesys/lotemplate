# OOTemplateFiller

use this script to automatically fill .odt templates with given values

## Requirements
- LibreOffice (the console-line version will be enough)
- a Java JRE
- the package `libreoffice-java-common`
- some python packages specified in `requirement.txt` that you can install with `pip install -r requirements.txt`

more informations on [the github page of unotools](https://github.com/t2y/unotools)

## Executing the script

Run the command
`soffice "--accept=socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"`
on your terminal or a server

Then run the script with the following arguments :
```
usage: main.py [-h] [--json [JSON]] [--output OUTPUT] [--config CONFIG] --host
               HOST --port PORT [--scan] [--force_replacement]
               template_file

positional arguments:
  template_file         Template file to scan or fill

optional arguments:
  -h, --help            show this help message and exit
  --json [JSON], -j [JSON]
                        Json file(s) that must fill the template, if any
  --output OUTPUT, -o OUTPUT
                        Name of the filled file, if the template should be
                        filled
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

All the specified files can be local or network-based

## Utilisation:
- text variables : putting '$variable' in the document is enough to add the variable 'variable'.
- image variables : add any image in the document, and put in the name of the image (properties) '$' followed by
  the desired name ('$image' for example to add the image 'image')
- dynamic arrays : allows you to add an unknown number of rows to the array.
  the array, but only on the last line. in the same way as for images, name your array variable
  with a '$' in front of it.

Get a file to fill with the `--scan` argument, and fill the fields you want. Add elements to the list
of an array to dynamically add rows

## Supported formats

| Format                  | ODT, OTT | DOC, DOCX | HTML | RTF | TXT | OTHER |
|-------------------------|----------|-----------|------|-----|-----|-------|
| text variables support  | ✅        | ✅         | ✅    | ✅   | ✅   | ❌     |
| image variables support | ✅        | ✅         | ✅    | ❌   | ❌   | ❌     |
| dynamic tables support  | ✅        | ❌         | ❌    | ❌   | ❌   | ❌     |

## Unsolvable problems

The error `main.com.sun.star.lang.DisposedException: Binary URP bridge disposed during call` happens frequently and 
unpredictably, and this error stops the soffice processus. This error, particularly annoying, is unfortunately 
impossible to fix, since it's a pyUNO - or soffice - bug, unresolved since 2015. It is therefore very unlikely that 
this bug will ever be fixed.
Here is a non-exhaustive list of cases that can cause this bug :
- The `.~lock.[FILENAME].odt#` file is present in the folder where the document is open.  This file is created when the 
  file is currently edited via libreoffice or openoffice, and deleted when the programs in which it is edited are 
  closed.
- The first line of the document is occupied by a table (juste jump a line, it will solve the problem)
- The background of document is an image, and is overlayed by many textfields

## Functionnal
- scans the template to extract the variables sheet
- Search for all possible errors before filling

## Non-functionnal
- filling the template
- export the template

## To do
1. Faire un CLI local (fin connecté à un serv sur lequel tourne libreoffice juste)
   - faire des tests unitaires
   - ajouter le filler texte
   - ajouter le filler tableaux
   - ajouter le filler graphique
   - ajouter l'export (pdf, docx, odt)
   - ajouter l'import docx et pdf - skipper les tableaux et les images, irréalisable en l'état
   - séparer le core de la couche CLI
   - débogger un max
2. en faire une API REST basée sur le même noyau avec flask
   - [se renseigner sur Flask](https://flask.palletsprojects.com/en/2.0.x/)
   - coder
3. implémenter l'API sur nemoweb
   - [se renseigner sur Ruby on Rails](https://www.eduonix.com/new_dashboard/Learn-Ruby-on-Rails-By-Building-Projects)
   - coder
    
## To consider

- la possibilitée de noter les variables de tableaux d'une autre manière (ex : '&') pour pouvoir placer
des variables statiques et des variables de tableau dynamiques, demander son avis à cyril dès son retour
- la possibilitée d'avoir des images dans les tableaux dynamiques
