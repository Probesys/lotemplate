Versions
========

Note : the upgrade from version 1.x to 2.x is easy. There is no reason to stay to version 1.x.

The upgrade documentation is in the file [UPGRADE.md](UPGRADE.md).

Versions 2.x
------------

- v2.0.0 : 01/01/2025 
  - BC Break (easy to fix) : see [UPGRADE.md](UPGRADE.md)
  - We can now generate Calc / Excel files (from Calc templates)
  - Is multiThreaded : we can generate several files at the same time
  - Performances improvements
  - No BC Breaks for the templates
  - upgrade debian, LibreOffice, Python libs versions
  - for devs : added "use bruno" requests inside the repository

Versions 1.x
------------

- v1.6.1 : 2024-04-12 : bugfix
  - fix the issue https://github.com/Probesys/lotemplate/issues/34 : too many endif bugg
- v1.6.0 : 2024-04-11
  - allow put variables inside headers and footers
  - fix a bug when a variable is both inside the text content and inside a table (it should not arrive, but it is fixed)
  - a new unit test system based on PDF converted to text in order to test contents that are not converted to text with a simple saveAs 
- v1.5.2 : 2024-02-24 : Better README
  - Rewrite for a betterdocker DockerFile without bug 
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

### Possible futur evolutions

- Possibly to add dynamic images in tables
- another way to make image variables that would be compatible with Microsoft Word and maybe other formats (example : set the variable name in the 'alternative text' field)
- key system for each institution for security
- handle bulleted lists using table like variables
- use variable formatting instead of the one of the character before
