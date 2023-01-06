# LOTemplateFiller

LOTemplateFiller is a script that fills a given document, used as a template, with elements given in a 
json file. This script can be used as an API (using Flask), a CLI or a python module for your own code.
For more information on a specific usage, read, the `Execute and use the API` or 
`Execute and use the CLI` section.

## Functionalities
- scans the template to extract the variables sheet
- search for all possible errors before filling
- filling the template
- export the filled template

## Requirements
For Docker use of the API, you can skip this step.

- LibreOffice (the console-line version will be enough)
- a Java JRE
- the package `libreoffice-java-common`
- some python packages specified in [requirement.txt](requirements.txt) that you can install with
  `pip install -r requirements.txt`. `Flask` and `Werkzeug` are optional, as they are used only for the API.

more information on [the GitHub page of unotools](https://github.com/t2y/unotools)

## Execute and use the API

Run the following command on your server :

```shell
python3 -m flask run
```

or simply

```shell
flask run
```

or, for Docker deployment:
```shell
docker-compose up
```


Then use the following routes :

*all routes take a secret key in the header, key `secret_key`, that correspond to the secret key configured in the 
[.env](.env) file. If no secret key is configured, the secret key isn't required at request.*

- `/`
  - `PUT` : take a directory name in the headers, key 'directory'. Creates a directory with the specified name
  - `GET` : returns the list of existing directories

- `/<directory>` : directory correspond to an existing directory
  - `GET` : returns a list of existing templates within the directory, with their scanned variables
  - `PUT` : take a file in the body, key 'file'. Uploads the given file in the directory, and returns the saved file 
    name and its scanned variables
  - `DELETE` : deletes the specified directory, and all its contents
  - `PATCH` : take a name in the headers, key 'name'. Rename the directory with the specified name.

- `/<directory>/<file>` : directory correspond to an existing directory, and file to an existing file within the 
  directory
  - `GET` : returns the file and the scanned variables of the file
  - `DELETE` : deletes the specified file
  - `PATCH` : take a file in the body, key 'file'. replace the existing file with the given file. 
    returns the file and the scanned variables of the file
  - `POST` : take a json in the raw body.
    fills the template with the values given in the json. returns the filled document(s).
- `/<directory>/<file>/download` : directory correspond to an existing directory, and file to an existing file within 
  the directory
  - `GET` : returns the original template file, as it was sent

you may wish to deploy the API on your server. 
[Here's how to do it](https://flask.palletsprojects.com/en/2.0.x/deploying/) - 
*but don't forget that you should have soffice installed on the server*

You can also change the flask options - like port and ip - in the [.flaskenv](.flaskenv) file.
If you're deploying the app with Docker, port and ip are editable in the [Dockerfile](Dockerfile).
You can also specify the host and port used to run and connect to soffice as command line arguments,
or in a config file (`config.yml`/`config.ini`/`config` or specified via --config).

## Execute and use the CLI

Run the script with the following arguments :
```
usage: lotemplate_cli.py [-h] [--json_file JSON_FILE [JSON_FILE ...]]
                         [--json JSON [JSON ...]] [--output OUTPUT]
                         [--config CONFIG] [--host HOST] [--port PORT]
                         [--scan] [--force_replacement] template_file

positional arguments:
  template_file         Template file to scan or fill

optional arguments:
  -h, --help            show this help message and exit
  --json_file JSON_FILE [JSON_FILE ...], -jf JSON_FILE [JSON_FILE ...]
                        Json files that must fill the template, if any
  --json JSON [JSON ...], -j JSON [JSON ...]
                        Json strings that must fill the template, if any
  --output OUTPUT, -o OUTPUT
                        Names of the filled files, if the template should
                        be filled. supported formats: pdf, html, docx, png, odt
  --config CONFIG, -c CONFIG
                        Configuration file path
  --host HOST           Host address to use for the libreoffice connection
  --port PORT           Port to use for the libreoffice connexion
  --scan, -s            Specify if the program should just scan the template
                        and return the information, or fill it.
  --force_replacement, -f
                        Specify if the program should ignore the scan's result
```

Args that start with '--' (e.g. --json) can also be set in a config file
(`config.yml`/`config.ini`/`config` or specified via --config). Config file syntax allows: key=value,
flag=true, stuff=[a,b,c] (for details, [see syntax](https://goo.gl/R74nmi)).
If an arg is specified in more than one place, then commandline values
override config file values which override defaults.

All the specified files can be local or network-based.

Get a file to fill with the `--scan` argument, and fill the fields you want. Add elements to the list
of an array to dynamically add rows. Then pass the file, and the completed json file(s) (using `--json_file`)
to fill it.

## Template Syntax
- text variables : putting '$variable' in the document is enough to add the variable 'variable'.
- image variables : add any image in the document, and put in the title of the alt text of the image
  (properties) '$' followed by the desired name ('$image' for example to add the image 'image')
- dynamic arrays : allows you to add an unknown number of rows to the array.
  the array, but only on the last line. Add the dynamic variables in the last row of the table, 
  exactly like text variables, but with a '&'

## Supported formats

### Import
| Format                  | ODT, OTT | HTML | DOC, DOCX | RTF | TXT | OTHER |
|-------------------------|----------|------|-----------|-----|-----|-------|
| text variables support  | ✅        | ✅    | ✅         | ✅   | ✅   | ❌     |
| dynamic tables support  | ✅        | ✅    | ✅         | ✅   | ❌   | ❌     |
| image variables support | ✅        | ✅    | ✅         | ❌   | ❌   | ❌     |

### Export
odt, pdf, html, docx.

Other formats can be easily added by adding the format information in the dictionary `formats` in 
[lotemplate/classes.py](lotemplate/classes.py) > Template > export().

Format information can be found on the 
[unoconv repo](https://github.com/unoconv/unoconv/blob/94161ec11ef583418a829fca188c3a878567ed84/unoconv#L391).

## Unsolvable problems

The error `UnoException` happens frequently and 
unpredictably, and this error stops the soffice processus 
(please note that the API try to re-launch the process by itself). This error, particularly annoying, is unfortunately 
impossible to fix, since it can be caused by multiples soffice (LibreOffice) bugs.
Here is a non-exhaustive list of cases that ***can*** cause this bug :
- The soffice process was simply closed after the connection is established.
- The `.~lock.[FILENAME].odt#` file is present in the folder where the document is open. This file is created when the 
  file is currently edited via libreoffice, and deleted when the programs in which it is edited are 
  closed. The program try to avoid this error by deleting this file at document opening.
- The first line of the document is occupied by a table or another dynamic element
  (just jump a line, it will solve the problem)
- The background of document is an image, and is overlaid by many text fields
- The document is an invalid file (e.g: the file is an image), and the bridge crashes instead of return the proper 
  error.

The amount of memory used by soffice can increase with its use, even when open files are properly closed (which is the 
case). Again, this is a bug in LibreOffice/soffice that has existed for years.

For trying to fix these problems, you can try:
- Use the most recent stable release of LibreOffice (less memory, more stable, fewer crashes)

## Useful elements
- [JODConverter wiki for list formats compatibles with LibreOffice](https://github.com/sbraconnier/jodconverter/wiki/Getting-Started)
- [The unoconv source code, written in python with PyUNO](https://github.com/unoconv/unoconv/blob/master/unoconv)
- [Unoconv source code for list formats - and properties - compatible with LibreOffice for export](https://github.com/unoconv/unoconv/blob/94161ec11ef583418a829fca188c3a878567ed84/unoconv#L391)
- [OpenOffice Python Bridge information and code exemples](http://www.openoffice.org/udk/python/python-bridge.html)
- [com.sun.star Java API docs (On which pyuno is based - but is not identical)](https://www.openoffice.org/api/docs/common/ref/com/sun/star/module-ix.html)
- [Java LibreOffice Programming Book](http://fivedots.coe.psu.ac.th/~ad/jlop)
- [Deploying Flask](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [Flask documentation - quickstart](https://flask.palletsprojects.com/en/2.0.x/quickstart/)
- [Flask documentation - upload](https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/)
    
## To consider

- Possibly to add dynamic images in tables
- another way to make image variables that would be compatible with Microsoft Word and maybe other formats (example : set the variable name in the 'alternative text' field)
- key system for each institution for security
- handle bulleted lists using table like variables
- use variable formatting instead of the one of the character before
