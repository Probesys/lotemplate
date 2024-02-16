LOTemplate (for Libre Office Template)
======================================

LOTemplate is document generator used to create documents programatically (ODT, DOCX, PDF) from a template and a json file.

Templates are Word or Libreoffice documents (ODT or DOCX).

```mermaid
flowchart LR
    template[Template<br/>in DOCX or ODT]
    json[Data<br/>JSON]
    lotemplate[LO Template]
    generatedFile[Generated File<br/>PDF, DOCX, ODT]
    
    template --> lotemplate
    json --> lotemplate
    lotemplate --> generatedFile
```

What makes this tool different from others are the following features :

* The templates are in DOCS or ODT format
* Template can have complex structures (variables, loop, conditions, counters, html,...)
* The tool can scan the template to extract the variables sheet
* The tool can be called by an API, a CLI or a python module.

The tool is written in Python and use a real LibreOffice headless to fill the templates.

Quick start
-----------

### Run the project with docker compose

Create a docker-compose.yml

```yaml
version: '3'
services:
  lotemplate:
    image: probesys38/lotemplate:v1.5.0
    volumes:
      - lotemplate-uploads:/app/uploads
    environment:
      - SECRET_KEY=lopassword
    command: "gunicorn -w 4 -b 0.0.0.0:8000 app:app"
```

run the service

```shell
docker-compose up -d
```

### Use the API

```bash
# creation of a directory
curl -X PUT -H 'secret_key: lopassword' -H 'directory: test_dir1' http://localhost:8000/
# {"directory":"test_dir1","message":"Successfully created"}
```

Let's imagine we have an file basic_test.odt (created by libreoffice) like this :

```
Test document

let’s see if the tag $my_tag is replaced and this $other_tag is detected.
[if $my_tag == foo]My tag is foo[endif]
[if $my_tag != foo]My tag is not foo[endif]
```

Upload this file to lotemplate

```bash
# upload a template
curl -X PUT -H 'secret_key: lopassword' -F file=@/tmp/basic_test.odt http://localhost:8000/test_dir1
# {"file":"basic_test.odt","message":"Successfully uploaded","variables":{"my_tag":{"type":"text","value":""},"other_tag":{"type":"text","value":""}}}

# generate a file titi.odt from a template and a json content
curl -X POST \
    -H 'secret_key: lopassword' \
    -H 'Content-Type: application/json' \
    -d '[{"name":"my_file.odt","variables":{"my_tag":{"type":"text","value":"foo"},"other_tag":{"type":"text","value":"bar"}}}]' \
    --output titi.odt http://localhost:8000/test_dir1/basic_test.odt 
```

After the operation, you get the file titi.odt with this content :

```
Test document

let’s see if the tag foo is replaced and this bar is detected.

My tag is foo

```

Installation
------------

### Requirements

For Docker use of the API, you can skip this step.

- LibreOffice (the console-line version will be enough)
- python3.8 or higher
- python3-uno
- some python packages specified in [requirement.txt](requirements.txt) that you can install with
  `pip install -r requirements.txt`. `Flask` and `Werkzeug` are optional, as they are used only for the API.

```bash
# on debian bookworm, you can use these commands
apt update
apt -y -t install bash python3 python3-uno python3-pip libreoffice-nogui
pip install -r requirements.txt
```

### Run the API

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

Basic Usage
-----------

### With the API

#### Examples of curl requests

```bash
# creation of a directory
curl -X PUT -H 'secret_key: my_secret_key' -H 'directory: test_dir1' http://lotemplate:8000/
# {"directory":"test_dir1","message":"Successfully created"}
curl -X PUT -H 'secret_key: my_secret_key' -H 'directory: test_dir2' http://lotemplate:8000/
# {"directory":"test_dir2","message":"Successfully created"}

# look at the created directories
curl -X GET -H 'secret_key: my_secret_key' http://lotemplate:8000/
# ["test_dir2","test_dir1"]

# delete a directory (and it's content
curl -X DELETE -H 'secret_key: my_secret_key' http://lotemplate:8000/test_dir2
# {"directory":"test_dir2","message":"The directory and all his content has been deleted"}

# look at the directories
curl -X GET -H 'secret_key: my_secret_key' http://lotemplate:8000/
# ["test_dir1"]
```

Let's imagine we have an odt file (created by libreoffice) like this :

```
Test document

let’s see if the tag $my_tag is replaced and this $other_tag is detected.
```

Upload this file to lotemplate

```bash
# upload a template
curl -X PUT -H 'secret_key: my_secret_key' -F file=@/tmp/basic_test.odt http://lotemplate:8000/test_dir1
{"file":"basic_test.odt","message":"Successfully uploaded","variables":{"my_tag":{"type":"text","value":""},"other_tag":{"type":"text","value":""}}}

# analyse an existing file and get variables
curl -X GET -H 'secret_key: my_secret_key'  http://lotemplate:8000/test_dir1/basic_test.odt
# {"file":"basic_test.odt","message":"Successfully scanned","variables":{"my_tag":{"type":"text","value":""},"other_tag":{"type":"text","value":""}}}

# generate a file titi.odt from a template and a json content
 curl -X POST -H 'secret_key: my_secret_key' -H 'Content-Type: application/json' -d '[{"name":"my_file.odt","variables":{"my_tag":{"type":"text","value":"foo"},"other_tag":{"type":"text","value":"bar"}}}]' --output titi.odt http://lotemplate:8000/test_dir1/basic_test.odt 
```

After the operation, you get the file titi.odt with this content :

```
Test document

let’s see if the tag foo is replaced and this bar is detected.
```

#### API reference

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



### Execute and use the CLI

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
flag=true, stuff=[a,b,c] (for details, [see syntax](https://pypi.org/project/ConfigArgParse/)).
If an arg is specified in more than one place, then commandline values
override config file values which override defaults.

All the specified files can be local or network-based.

Get a file to fill with the `--scan` argument, and fill the fields you want. Add elements to the list
of an array to dynamically add rows. Then pass the file, and the completed json file(s) (using `--json_file`)
to fill it.


Template Syntax
---------------

### text variables

Put `$variable` in the document is enough to add the variable 'variable'.

A variable name is only composed by chars, letters or underscores.

You can also use "function variables". It is exactly the same as simple variables
but with a syntax that allows you a more flexible variable name :

examples :

```
# simple variable
$my_var
$MyVar99_2020

# basic function variable
$my_var(firstName)
$my_var(address.city)

# you have to escape parenthesis inside the parameter in the
# variable name with a backslash
$my_var(firstName\(robert\))
```

Then in the json, function variable are working exactly like simple variables.

```json
{
  "my_var": {
    "type": "text",
    "value": "my value"
  },
  "MyVar99_2020": {
    "type": "text",
    "value": "my value"
  },
  "my_var(firstName)": {
    "type": "text",
    "value": "my value"
  },
  "my_var(address.city)": {
    "type": "text",
    "value": "my value"
  },
  "my_var(firstName\\(robert\\))": {
    "type": "text",
    "value": "my value"
  }
}
```

### html variables

Html variables are exactly like text variables, but the html is interpreted when
the variable is replaced in the document.

To declare a variable as an html variable, we only have to change the type in the json and send "html" instead of "text".

```json
{
  "my_var": {
    "type": "html",
    "value": "my value with <strong>html formatting</strong>"
  }
}
```

Limitation : Html is not interpreted into "shape content". For example for a text associated to a rectangle inserted into the document.

### image variables

Add any image in the document, and put in the title of the alt text of the image
(properties) '$' followed by the desired name ('$image' for example to add the image 'image')

### dynamic arrays

You can add an unknown number of rows to the array but only on the last line.
Add the dynamic variables in the last row of the table, exactly like text variables, but with a '&' instead of a the '$'

### if statement

You can use if statement in order to display or to hide a part of your document.

There is many operators : 

* `==` : test if the var is equal to the value (case-insensitive)
* `!=` : test if the var is not equal to the value (case-insensitive)
* `===` : test if the var is equal to the value (case-sensitive)
* `!==` : test if the var is not equal to the value (case-sensitive)
* `IS_EMPTY` : check if the var is empty (empty means empty or only spaces, tabs or newlines)
* `IS_NOT_EMPTY` : check if the var is not empty (empty means empty or only spaces, tabs or newlines)
* `CONTAINS` : check if the var contains the value (case-insensitive)
* `NOT_CONTAINS` : check if the var does not contain the value (case-insensitive)

```
[if $my_var == my_value]
$my_var equals my_value (case insensitive)
[endif]

[if $my_var === my_value]
$my_var equals my_value (case sensitive)
[endif]

[if $my_var != my_value]
$my_var does not equals my_value (case insensitive)
[endif]

[if $my_var !== my_value]
$my_var does not equals my_value (case sensitive)
[endif]

[if $my_var CONTAINS y_VAl]
This part will be displayed if $my_var contains y_VAl (case insensitive)
[endif]

[if $my_var NOT_CONTAINS dlfksqjqm]
This part will be displayed if $my_var does not contain dlfksqjqm
[endif]

[if $my_var IS_EMPTY]
This part will be displayed if my_var is empty (empty means empty or only spaces, tabs or newlines)
[endif]

[if $my_var IS_NOT_EMPTY]
This part will be displayed if my_var is empty (empty means empty or only spaces, tabs or newlines)
[endif]
```

You can put an if statement inside another if statement

```
[if $foo == my_value]
[if $bar == my_value2]
here you have your document
[endif]
[if $bar == my_value3]
here you have your document
[endif]
[endif]
```

### for statement

You can use for statement in order to display a part of your
document multiple times.

WARNING : the for system loses the formating of the template. If you want a
specific formating, you have to put it in an HTML statement.

You have to send an array in the json file with a dict inside the array

```json
{
  "tutu": {
    "type": "array",
    "value": [
      {
        "firstName": "perso 1",
        "lastName": "string 1",
        "address": {
          "street1": "8 rue de la paix",
          "street2": "",
          "zip": "75008",
          "city": "Paris",
          "state": "Ile de France"
        }
      },
      {
        "firstName": "perso 2",
        "lastName": "lastname with < and >",
        "address": {
          "street1": "12 avenue Jean Jaurès",
          "street2": "",
          "zip": "38000",
          "city": "Grenoble",
          "state": "Isère"
        }
      }
    ]
  }
}
```

Then in your template file you can use the for like this :

```
Tests of for statements

[for $tutu]
Associate number [forindex]
first name : [foritem firstName] 
last name escaped by default [foritem lastName]
last name escaped html [foritem lastName escape_html]
last name not escaped [foritem lastName raw]
Address : 
[foritem address.street1]
[foritem address.zip] [foritem address.city]
[endfor]
```

* `[forindex]` : this is a counter beginning at 0 indicating the iteration count.
* `[foritem firstName]` : variable firstName of the current iteration.
* `[foritem lastName escape_html]` : variable lastName of the current iteration escaped by html.
* `[foritem lastName raw]` : variable lastName of the current iteration not escaped.
* `[foritem address.street1]` : variable address.street1 of the current iteration when you have a hierarchy

Note : you can use if inside for statements

Here we display only the people living in Grenoble
```
[for $tutu]
[if [foritem address.city] == Grenoble]
first name : [foritem firstName] 
last name : [foritem lastName]
Address : 
[foritem address.street1]
[foritem address.zip] [foritem address.city]
[endif]
[endfor]
```

Here we display only the first element of the array
```
[for $tutu]
[if [forindex] == 0]
first name : [foritem firstName] 
last name : [foritem lastName]
[endif]
[endfor]
```

Note : If you are using `[forindex]` inside a variable name, the variable
is excluded from the parsing of the template. It allows you to create a
dynamic variable name inside a for loop. Ex : `$my_var(people.[forindex].name)` is
excluded from the variable parsing.

### html statement

You can use html statement in order to display a part of your document with a specific formating.

Here is some examples that ca be use inside an odt template

```
[html]
<table>
<tr>
  <td>First Name</td>
  <td>Last Name</td>
</tr>
<tr>
  <td>First Name</td>
  <td>Last Name</td>
</tr>
</table>
[endhtml]
```

Then all the html content is interpreted and pasted as html. It is then rendered
as a formated text (a table in this example) inside the document.

You can also display a variable that contains an html content inside an html statement

```
[html]
$my_html_variable
[endhtml]
```

with the associated json :

```json
{
  "tutu": {
    "type": "text",
    "value": "my <strong>html formated</strong> content"
  }
}
```

As the for statement removes formatting, you can use the html statement combined with the
for statement to display a table with a specific formating.

Let's see an example with the following json :

```json
{
  "tutu": {
    "type": "array",
    "value": [
      {
        "firstName": "perso 1",
        "lastName": "string 1",
        "address": {
          "street1": "8 rue de la paix",
          "street2": "",
          "zip": "75008",
          "city": "Paris",
          "state": "Ile de France"
        }
      },
      {
        "firstName": "perso 2",
        "lastName": "lastname with < and >",
        "address": {
          "street1": "12 avenue Jean Jaurès",
          "street2": "",
          "zip": "38000",
          "city": "Grenoble",
          "state": "Isère"
        }
      }
    ]
  }
}
```

and the odt template :

```
[html]
<table>
<tr>
  <td>First Name</td>
  <td>Last Name</td>
</tr>
[for $tutu]
<tr>
  <td>[foritem firstName escape_html]</td>
  <td>[foritem lastName escape_html]</td>
</tr>
[endfor]
</table>
[endhtml]
```

### counter statement

You can use counter statement in order to display values that will be incremented step by step in your document. It
can be used for example to have a heading automatic numbering.

**WARNING** : generally you don't have to use this counter feature. You can use the automatic numbering of Word or Libre Office

#### basic usage of counter

In your odt, you can use :

```
chapter [counter chapter] : introduction

chapter [counter chapter] : context

[counter paragraph] : geopolitical context

[counter paragraph] : geographical context

[counter paragraph] : economical context

chapter [counter chapter] : analysis
[counter.reset paragraph]
[counter paragraph] : geopolitical analysis

[counter paragraph] : geographical analysis

[counter paragraph] : economical analysis
```

It will be transformed in : 

```
chapter 1 : introduction

chapter 2 : context

1 : geopolitical context

2 : geographical context

3 : economical context

chapter 3 : analysis

1 : geopolitical analysis

2 : geographical analysis

3 : economical analysis
```

The possible syntaxe are :

* `[counter counter_name]` : increment the counter "counter_name" and display it
* `[counter counter_name hidden]` : increment the counter "counter_name" without displaying it
* `[counter.reset counter_name]` : reset the counter "counter_name" to 0
* `[counter.last counter_name]` : display the last value of the counter "counter_name" without incrementing it
* `[counter.format counter_name format_name]` : change the format of the counter
    * `[counter.format counter_name number]` : the counter is displayed as a number (default)
    * `[counter.format counter_name letter_lowercase]` : the counter is displayed as a letter (a, b, c, ...)
    * `[counter.format counter_name letter_uppercase]` : the counter is displayed as a letter (A, B, C, ...)


#### You can display hierarchical counters by just using `counter.last`:

```
chapter [counter chapter] : introduction

chapter [counter chapter] : context

[counter.last chapter].[counter paragraph] : geopolitical context

[counter.last chapter].[counter paragraph] : geographical context

[counter.last chapter].[counter paragraph] : economical context

chapter [counter chapter] : analysis
[counter.reset paragraph]
[counter.last chapter].[counter paragraph] : geopolitical analysis

[counter.last chapter].[counter paragraph] : geographical analysis

[counter.last chapter].[counter paragraph] : economical analysis
```

The result will be

```
chapter 1 : introduction

chapter 2 : context

2.1 : geopolitical context

2.2 : geographical context

2.3 : economical context

chapter 3 : analysis

3.1 : geopolitical analysis

3.2 : geographical analysis

3.3 : economical analysis
```

#### count the number of elements of a list

```
[counter.reset iterator]

[for $solutions]

Title : [foritem title]

Content : [foritem paragraph]

[counter iterator hidden]
[endfor]

we displayed [counter.last iterator] solutions
```


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

Doc for developpers of lotemplate
---------------------------------

### Run the tests

You need to have docker and docker-compose installed and then run

```bash
make tests
```

### Installation with Docker for dev when your uid is not 1000

for this we use fixuid (https://github.com/boxboat/fixuid)

you have to define two env variable MY_UID and MY_GID with your uid and gid
copy docker-compose.override.yml.example to docker-compose.override.yml

```shell
export MY_UID=$(id -u)
export MY_GID=$(id -g)
cp docker-compose.override.yml.example docker-compose.override.yml
docker-compose up
```

Unsolvable problems
-------------------

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

Useful elements
---------------

- [JODConverter wiki for list formats compatibles with LibreOffice](https://github.com/sbraconnier/jodconverter/wiki/Getting-Started)
- [The unoconv source code, written in python with PyUNO](https://github.com/unoconv/unoconv/blob/master/unoconv)
- [Unoconv source code for list formats - and properties - compatible with LibreOffice for export](https://github.com/unoconv/unoconv/blob/94161ec11ef583418a829fca188c3a878567ed84/unoconv#L391)
- [OpenOffice Python Bridge information and code exemples](http://www.openoffice.org/udk/python/python-bridge.html)
- [com.sun.star Java API docs (On which pyuno is based - but is not identical)](https://www.openoffice.org/api/docs/common/ref/com/sun/star/module-ix.html)
- [Java LibreOffice Programming Book](http://fivedots.coe.psu.ac.th/~ad/jlop)
- [Deploying Flask](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [Flask documentation - quickstart](https://flask.palletsprojects.com/en/2.0.x/quickstart/)
- [Flask documentation - upload](https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/)
    
To consider
-----------

- Possibly to add dynamic images in tables
- another way to make image variables that would be compatible with Microsoft Word and maybe other formats (example : set the variable name in the 'alternative text' field)
- key system for each institution for security
- handle bulleted lists using table like variables
- use variable formatting instead of the one of the character before

Versions
--------
- v1.5.1 : 2024-02-16 : Better README
  - Rewriting of the README file
- v1.5.0 : 2024-02-12 : syntax error detection
  - add syntax error detection in if statements
  - add syntax error detection in for statements
  - come back to default libreoffice of Debian Bookworm (removed backports, incompatibility)
- v1.4.1 : 2023-11-20 : micro-feature for counter and fix possible bug
  - use counters for counting elements of a list
  - fix possible bug with reset and last.
- v1.4.0, 2023-11-17 : counters
  - add a counter system inside templates
  - add better scan for if statement. Raises an error if there is too many endif in the template.
  - speedup html statement replacement and scanning
  - speedup for statement replacement and scanning
  - tests of for scanning
  - internal : add scan testing inside content unit tests
- v1.3.0, 2023-11-16 :
  - major refactoring. No evolution for the user.
  - new unit tests on tables and images
  - no BC Break (theoretically)
- v1.2.8, 2023-09-01 :
  - fix bug in TextShape var replacement
- v1.2.7, 2023-08-30 :
  - Upgrade to debian bookworm slim
- v1.2.6, 2023-08-30 :
  - new comparators for if statements : ===, !==, CONTAINS, NOT_CONTAINS
  - variables of type "html" are now supported and copied as HTML
- v1.2.5, 2023-07-17 : temporary fix for detecting endhtml and endfor
- v1.2.4, 2023-07-09 : fix major bug in if statement scanning
- v1.2.3, 2023-07-07 : no endif detection, performance improvement in if statement
- v1.2.2, 2023-06-09 : bugfix html statement scan missing
- v1.2.1, 2023-06-05 : little fix for CI
- v1.2.0, 2023-06-04 : if statements inside for
- v1.1.0, 2023-05-23 : recursive if statement
- v1.0.1, 2023-05-05 : workaround, fix in html formatting
- v1.0.0, 2023-05-03 : if statement, for statement, html statement
- not numbered : about may 2022 : first version
