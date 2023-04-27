"""
Copyright (C) 2023 Probesys


The classes used for document connexion and manipulation
"""

__all__ = (
    'Connexion',
    'Template',
)

import os
from typing import Union
from urllib import request
from PIL import Image
from sorcery import dict_of

import uno
import re
import unohelper
from com.sun.star.beans import PropertyValue, UnknownPropertyException
from com.sun.star.io import IOException
from com.sun.star.lang import IllegalArgumentException, DisposedException
from com.sun.star.connection import NoConnectException
from com.sun.star.uno import RuntimeException
from com.sun.star.awt import Size
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.style.BreakType import PAGE_AFTER

from . import errors
from .utils import *


class Connexion:

    def __repr__(self):
        return (
            f"<Connexion object :'host'={self.host!r}, 'port'={self.port!r}, "
            f"'local_ctx'={self.local_ctx!r}, 'ctx'={self.local_ctx!r}, 'desktop'={self.desktop!r}, "
            f"'graphic_provider'={self.graphic_provider!r}>"
        )

    def __str__(self):
        return f"Connexion host {self.host}, port {self.port}"

    def __init__(self, host: str, port: str):
        """
        An object representing the connexion between the script and the LibreOffice/OpenOffice processus

        :param host: the address of the host to connect to
        :param port: the host port to connect to
        """

        self.host = host
        self.port = port
        self.local_ctx = uno.getComponentContext()
        try:
            self.ctx = self.local_ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", self.local_ctx
            ).resolve(f"uno:socket,host={host},port={port};urp;StarOffice.ComponentContext")
        except (NoConnectException, RuntimeException) as e:
            raise errors.UnoException(
                'connection_error',
                f"Couldn't find/connect to the soffice process on \'{host}:{port}\'. "
                f"Make sure the soffice process is correctly running with correct host and port informations. "
                f"Read the README file, section 'Executing the script' for more informations about how to "
                f"run the script.", dict_of(host, port)
            ) from e
        self.desktop = self.ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self.ctx)
        self.graphic_provider = self.ctx.ServiceManager.createInstance('com.sun.star.graphic.GraphicProvider')

    def restart(self) -> None:
        """
        Restart the connexion

        :return: None
        """

        self.__init__(self.host, self.port)


class IfStatement:
    """
    Class representing an if statement in a template libreoffice
    """
    start_regex = r"""
        \[\s*if\s*          # [if detection
          \$                # var start with $
          (\w+              # basic var name
            (\(             # parsing of fonction var
              ((?:          # ?: is for non capturing group : the regex inside the parenthesis must be matched but does not create the capturing group
                \\.|.       # everything that is escaped or every simple char
              )*?)          # the ? before the ) in order to be not greedy (stop on the first unescaped ")"
            \))
          ?)                # the ? before the ) in order to be not greedy (won't go until the last ")")
          \s*
          (                 # catch whether
              (?:           # for syntax == var or != var
                  (              # equality
                    \=\=|
                    \!\=
                  )\s*
                  (                 # value is anything, should escape [ and ]
                    (?:
                      \\.|.
                    )*
                  ?)                # not too greedy
              )
              |
              (IS_EMPTY|IS_NOT_EMPTY) # for syntax [if $toto IS_EMPTY] or [if $toto IS_NOT_EMPTY]
          )
        \s*\]
    """
    # remove comments, spaces and newlines
    start_regex = re.sub(r'#.*', '', start_regex).replace("\n", "").replace("\t", "").replace(" ", "")
    # print(start_regex)
    # \[\s*if\s*\$(\w+(\(((?:\\.|.)*?)\))?)\s*((?:(\=\=|\!\=)\s*((?:\\.|.)*?))|(IS_EMPTY|IS_NOT_EMPTY))\s*\]

    end_regex = r'\[\s*endif\s*\]'

    def __init__(self, if_string):
        self.if_string = if_string
        match = re.search(self.start_regex, if_string, re.IGNORECASE)
        self.variable_name = match.group(1)
        if match.group(5) is not None:
            # syntaxes like [if $foo == bar] or [if $foo != bar]
            self.operator = match.group(5)
            self.value = match.group(6)
        else:
            # syntaxes like [if $foo IS_EMPTY] or [if $foo IS_NOT_EMPTY]
            self.operator = match.group(7)

    def get_if_result(self, value):
        if self.operator == '==':
            return value == self.value
        if self.operator == '!=':
            return value != self.value
        if self.operator == 'IS_EMPTY':
            return re.search(r'^[\s\t\n]*$', value) is not None
        if self.operator == 'IS_NOT_EMPTY':
            return re.search(r'^[\s\t\n]*$', value) is None
        return False


class ForStatement:
    """
    Class representing an for statement in a template libreoffice
    """
    start_regex = r"""
        \[\s*for\s*          # [if detection
          \$                # var start with $
          (\w+              # basic var name
            (\(             # parsing of fonction var
              ((?:          # ?: is for non capturing group : the regex inside the parenthesis must be matched but does not create the capturing group
                \\.|.       # everything that is escaped or every simple char
              )*?)          # the ? before the ) in order to be not greedy (stop on the first unescaped ")"
            \))
          ?)                # the ? before the ) in order to be not greedy (won't go until the last ")")
        \s*\]
    """
    # remove comments, spaces and newlines
    start_regex = re.sub(r'#.*', '', start_regex).replace("\n", "").replace("\t", "").replace(" ", "")
    # print(start_regex)
    # \[\s*for\s*\$(\w+(\(((?:\\.|.)*?)\))?)\s*\]
    foritem_regex = r"""
        \[\s*foritem\s*          # [foritem detection
            (
                \w+              # simple var of type abc
                (?:\.\w+)*       # composite var name like abc.def
            )
            (?:\s+(escape_html|raw))?   # option pour escaper le contenu de la variable
        \s*\]
    """
    foritem_regex = re.sub(r'#.*', '', foritem_regex).replace("\n", "").replace("\t", "").replace(" ", "")
    # print(foritem_regex)
    # \[\s*foritem\s*((\w+)(?:\.\w+)*)\s*\]

    # [forindex] is replaced by the counter of the loop. A string starting at 0
    forindex_regex = r'\[\s*forindex\s*\]'

    end_regex = r'\[\s*endfor\s*\]'

    def __init__(self, for_string):
        self.for_string = for_string
        match = re.search(self.start_regex, for_string, re.IGNORECASE)
        self.variable_name = match.group(1)

class HtmlStatement:
    """
    Class representing an html statement in a template libreoffice
    """
    start_regex = r'\[\s*html\s*\]'
    end_regex = r'\[\s*endhtml\s*\]'
    def __init__(self, html_string):
        self.html_string = html_string


class Template:

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        return str(self.file_name)

    def __repr__(self):
        return repr(self.file_url)

    def __getitem__(self, item):
        return self.variables[item] if self.variables else None

    def __init__(self, file_path: str, cnx: Connexion, should_scan: bool):
        """
        An object representing a LibreOffice/OpenOffice template that you can fill, scan, export and more

        :param file_path: the path of the document
        :param cnx: the connection object to the bridge
        :param should_scan: indicates if the document should be scanned at initialisation
        """

        self.cnx = cnx
        self.file_name = file_path.split("/")[-1]
        self.file_dir = "/".join(file_path.split("/")[:-1])
        self.file_path = file_path
        self.file_url = get_file_url(file_path)
        self.new = None
        self.variables = None
        self.doc = None
        try:
            os.remove(self.file_dir + "/.~lock." + self.file_name + "#")
        except FileNotFoundError:
            pass
        try:
            self.doc = self.cnx.desktop.loadComponentFromURL(self.file_url, "_blank", 0, ())
        except DisposedException as e:
            self.close()
            raise errors.UnoException(
                'bridge_exception',
                f"The connection bridge on '{self.cnx.host}:{self.cnx.port}' crashed on file opening."
                f"Please restart the soffice process. For more informations on what caused this bug and how to avoid "
                f"it, please read the README file, section 'Unsolvable Problems'.",
                dict_of(cnx.host, cnx.port)
            ) from e
        except IllegalArgumentException:
            self.close()
            raise errors.FileNotFoundError(
                'file_not_found',
                f"the given file does not exist or has not been found (file {file_path!r})",
                dict_of(file_path)
            ) from None
        except RuntimeException as e:
            self.close()
            raise errors.UnoException(
                'connection_closed',
                f"The previously established connection with the soffice process on '{self.cnx.host}:{self.cnx.port}' "
                f"has been closed, or ran into an unknown error. Please restart the soffice process, and retry.",
                dict_of(cnx.host, cnx.port)
            ) from e

        if not self.doc or not self.doc.supportsService('com.sun.star.text.GenericTextDocument'):
            self.close()
            raise errors.TemplateError(
                'invalid_format',
                f"The given format ({self.file_name.split('.')[-1]!r}) is invalid, or the file is already open by "
                f"an other process (accepted formats: ODT, OTT, DOC, DOCX, HTML, RTF or TXT)",
                dict(format=self.file_name.split('.')[-1])
            )
        self.variables = self.scan(should_close=True) if should_scan else None

    def scan(self, **kwargs) -> dict[str: dict[str, Union[str, list[str]]]]:
        """
        scans the variables contained in the template. Supports text, tables and images

        :return: list containing all the variables founded in the template
        """

        should_close = kwargs.get("should_close", False)

        def scan_text(doc) -> dict[str, dict[str, str]]:
            """
            scan for text in the given doc

            :param doc: the document to scan
            :return: the scanned variables
            """

            raw_string = doc.getText().getString()

            matches = var_regexes['text'].finditer(raw_string)
            plain_vars = {}
            for var in matches:
                key_name = var[0][1:]
                # add to plain_vars if it doesn't matche ForStatement.foritem_regex
                my_match = re.match(ForStatement.forindex_regex, key_name)
                if not re.search(ForStatement.forindex_regex, key_name, re.IGNORECASE):
                    plain_vars[key_name] = {'type': 'text', 'value': ''}

            text_fields_vars = {}
            for page in doc.getDrawPages():
                for shape in page:
                    try:
                        matches = var_regexes['text'].finditer(shape.String)
                    except (AttributeError, UnknownPropertyException):
                        continue
                    text_fields_vars = (text_fields_vars |
                                        {var.group(0)[1:]: {'type': 'text', 'value': ''} for var in matches})

            for var in scan_table(doc, get_list=True):
                if '$' + var in plain_vars:
                    del plain_vars[var]

            for var in scan_for(doc):
                if var in plain_vars:
                    del plain_vars[var]

            return plain_vars | text_fields_vars

        def scan_if(doc) -> None:
            """
            scan for if statement. No return. We just verify that there is
            and endif for each if statement
            """

            def scan_single_if(local_x_found):
                """
                scan for a single if statement
                """
                if_statement = IfStatement(local_x_found.getString())
                position_in_text = len(if_statement.if_string)
                text = local_x_found.getText()
                cursor = text.createTextCursorByRange(local_x_found)
                if not cursor.goRight(1, True):
                    raise errors.TemplateError(
                        'no_endif_found',
                        f"The statement {if_statement} has no endif",
                        dict_of(if_statement)
                    )
                position_in_text += 1
                selected_string = cursor.String
                match = re.search(IfStatement.end_regex, selected_string, re.IGNORECASE)
                while match is None:
                    if not cursor.goRight(1, True):
                        raise errors.TemplateError(
                            'no_endif_found',
                            f"The statement {if_statement} has no endif",
                            dict_of(if_statement)
                        )
                    position_in_text = position_in_text + 1
                    selected_string = cursor.String
                    match = re.search(IfStatement.end_regex, selected_string, re.IGNORECASE)

            search = doc.createSearchDescriptor()
            search.SearchString = IfStatement.start_regex
            search.SearchRegularExpression = True
            search.SearchCaseSensitive = False
            x_found = doc.findFirst(search)
            while x_found is not None:
                scan_single_if(x_found)
                x_found = doc.findNext(x_found.End, search)

        def scan_for(doc) -> dict:
            """
            scan for statement. return list of vars.

            We verify that
            - there is and endfor for each for statement
            - vars sent are lists
            """

            def scan_single_for(local_x_found) -> str:
                """
                scan for a single for statement
                """
                for_statement = ForStatement(local_x_found.getString())
                position_in_text = len(for_statement.for_string)
                text = local_x_found.getText()
                cursor = text.createTextCursorByRange(local_x_found)
                if not cursor.goRight(1, True):
                    raise errors.TemplateError(
                        'no_endfor_found',
                        f"The statement {for_statement} has no endfor",
                        dict_of(for_statement)
                    )
                position_in_text += 1
                selected_string = cursor.String
                match = re.search(ForStatement.end_regex, selected_string, re.IGNORECASE)
                while match is None:
                    if not cursor.goRight(1, True):
                        raise errors.TemplateError(
                            'no_endfor_found',
                            f"The statement {for_statement} has no endfor",
                            dict_of(for_statement)
                        )
                    position_in_text = position_in_text + 1
                    selected_string = cursor.String
                    match = re.search(ForStatement.end_regex, selected_string, re.IGNORECASE)
                return for_statement.variable_name

            search = doc.createSearchDescriptor()
            search.SearchString = ForStatement.start_regex
            search.SearchRegularExpression = True
            search.SearchCaseSensitive = False
            x_found = doc.findFirst(search)

            for_vars = {}
            while x_found is not None:
                variable_name = scan_single_for(x_found)
                for_vars[variable_name] = {'type': 'array', 'value': []}
                x_found = doc.findNext(x_found.End, search)
            return for_vars

        def scan_html(doc) -> None:
            """
            scan html statement.

            We verify that
            - there is and endhtml for each html statement
            """

            def scan_single_html(local_x_found) -> None:
                """
                scan for a single for statement
                """
                html_statement = HtmlStatement(local_x_found.getString())
                position_in_text = len(html_statement.html_string)
                text = local_x_found.getText()
                cursor = text.createTextCursorByRange(local_x_found)
                if not cursor.goRight(1, True):
                    raise errors.TemplateError(
                        'no_endhtml_found',
                        f"The statement {html_statement} has no endfor",
                        dict_of(html_statement)
                    )
                position_in_text += 1
                selected_string = cursor.String
                match = re.search(HtmlStatement.end_regex, selected_string, re.IGNORECASE)
                while match is None:
                    if not cursor.goRight(1, True):
                        raise errors.TemplateError(
                            'no_endhtml_found',
                            f"The statement {html_statement} has no endfor",
                            dict_of(html_statement)
                        )
                    position_in_text = position_in_text + 1
                    selected_string = cursor.String
                    match = re.search(HtmlStatement.end_regex, selected_string, re.IGNORECASE)

            search = doc.createSearchDescriptor()
            search.SearchString = HtmlStatement.start_regex
            search.SearchRegularExpression = True
            search.SearchCaseSensitive = False
            x_found = doc.findFirst(search)

            while x_found is not None:
                scan_single_html(x_found)
                x_found = doc.findNext(x_found.End, search)

        def scan_table(doc, get_list=False) -> Union[dict, list]:
            """
            scan for tables in the given doc

            :param get_list: indicates if the function should return a list
            of variables or the formatted dictionary of variables
            :param doc: the document to scan
            :return: the scanned variables
            """

            def scan_cell(cell) -> None:
                """
                scan for variables in the given cell

                :param cell: the cell to scan
                :return: None
                """
                for match in var_regexes['table'].finditer(cell):
                    if not match.captures('var'):
                        continue
                    if row_i != nb_rows - 1:
                        raise errors.TemplateError(
                            'variable_not_in_last_row',
                            f"The variable {match[0]!r} (table {t_name!r}) "
                            f"isn't in the last row (got: row {row_i + 1!r}, "
                            f"expected: row {nb_rows!r})",
                            dict(table=t_name, actual_row=row_i + 1,
                                 expected_row=nb_rows, variable=match[0])
                        )
                    tab_vars[match[0][1:]] = {'type': 'table', 'value': ['']}
                    list_tab_vars.append(match[0])

            tab_vars = {}
            list_tab_vars = []
            for i in range(doc.getTextTables().getCount()):
                table_data = doc.getTextTables().getByIndex(i).getDataArray()
                t_name = doc.getTextTables().getByIndex(i).getName()
                nb_rows = len(table_data)
                for row_i, row in enumerate(table_data):
                    for column in row:
                        scan_cell(column)

            return list_tab_vars if get_list else tab_vars

        def scan_image(doc) -> dict[str, dict[str, str]]:
            """
            scan for images in the given doc

            :param doc: the document to scan
            :return: the scanned variables
            """

            return {
                elem.LinkDisplayName[1:]: {'type': 'image', 'value': ''}
                for elem in doc.getGraphicObjects()
                if var_regexes['image'].fullmatch(elem.LinkDisplayName)
            }

        texts = scan_text(self.doc)
        scan_if(self.doc)
        tables = scan_table(self.doc)
        images = scan_image(self.doc)
        fors = scan_for(self.doc)

        variables_list = list(texts.keys()) + list(tables.keys()) + list(images.keys()) + list(fors.keys())
        duplicates = [variable for variable in variables_list if variables_list.count(variable) > 1]

        if duplicates:
            first_type = "text" if duplicates[0] in texts.keys() else "image"
            second_type = "table" if duplicates[0] in tables.keys() else "image"
            if should_close:
                self.close()
            raise errors.TemplateError(
                'duplicated_variable',
                f"The variable {duplicates[0]!r} is mentioned two times, but "
                f"for two different types: {first_type!r}, and {second_type!r}",
                dict_of(first_type, second_type, variable=duplicates[0])
            )

        return texts | tables | images | fors

    def search_error(self, json_vars: dict[str, dict[str, Union[str, list[str]]]]) -> None:
        """
        find out which variable is a problem, and raise the required error

        :param json_vars: the given json variables
        :return: None
        """

        if json_vars == self.variables:
            return

        json_missing = [key for key in set(self.variables) - set(json_vars)]
        if json_missing:
            raise errors.JsonComparaisonError(
                'missing_required_variable',
                f"The variable {json_missing[0]!r}, present in the template, "
                f"isn't present in the json.",
                dict(variable=json_missing[0])
            )

        template_missing = [key for key in set(json_vars) - set(self.variables)]
        if template_missing:
            raise errors.JsonComparaisonError(
                'unknown_variable',
                f"The variable {template_missing[0]!r}, present in the json, isn't present in the template.",
                dict(variable=template_missing[0])
            )

        json_incorrect = [key for key in json_vars if json_vars[key]['type'] != self.variables[key]['type']]
        if json_incorrect:
            raise errors.JsonComparaisonError(
                'incorrect_value_type',
                f"The variable {json_incorrect[0]!r} should be of type "
                f"{self.variables[json_incorrect[0]]['type']!r}, like in the template, but is of type "
                f"{json_vars[json_incorrect[0]]['type']!r}",
                dict(variable=json_incorrect[0], actual_variable_type=json_vars[json_incorrect[0]]['type'],
                     expected_variable_type=self.variables[json_incorrect[0]]['type'])
            )

        raise errors.JsonComparaisonError(
            'unknown_reason',
            f"Variables given in the json don't match with the given template, but no reason was found", {})

    def fill(self, variables: dict[str, dict[str, Union[str, list[str]]]]) -> None:
        """
        Fills a template copy with the given values

        :param variables: the values to fill in the template
        :return: None
        """

        def html_replace(doc) -> None:
            """
            Replace the content inside [html] and [endhtml] with a pasted html code inside the doc
            """

            def compute_html(doc, local_x_found):
                html_statement = HtmlStatement(local_x_found.getString())
                text = local_x_found.getText()
                cursor = text.createTextCursorByRange(local_x_found)
                cursor.goRight(1, True)
                selected_string = cursor.String
                match = re.search(HtmlStatement.end_regex, selected_string, re.IGNORECASE)
                while match is None:
                    cursor.goRight(1, True)
                    selected_string = cursor.String
                    match = re.search(HtmlStatement.end_regex, selected_string, re.IGNORECASE)
                cursor.String = ''
                html_string = re.sub(HtmlStatement.end_regex, '', selected_string, flags=re.IGNORECASE)
                html_string = re.sub(HtmlStatement.start_regex, '', html_string, flags=re.IGNORECASE)
                input_stream = self.cnx.ctx.ServiceManager.createInstanceWithContext("com.sun.star.io.SequenceInputStream", self.cnx.ctx)
                input_stream.initialize((uno.ByteSequence(html_string.encode()),))
                prop1 = PropertyValue()
                prop1.Name = "FilterName"
                prop1.Value = "HTML (StarWriter)"
                prop2 = PropertyValue()
                prop2.Name = "InputStream"
                prop2.Value = input_stream
                cursor.insertDocumentFromURL("private:stream", (prop1, prop2))

            # main of for_replace
            search = doc.createSearchDescriptor()
            search.SearchString = HtmlStatement.start_regex
            search.SearchRegularExpression = True
            search.SearchCaseSensitive = False
            x_found = doc.findFirst(search)
            while x_found is not None:
                compute_html(doc, x_found)
                x_found = doc.findNext(x_found.End, search)

        def for_replace(doc, local_variables: dict[str, dict[str, Union[str, list[str]]]]) -> None:
            """
            Parse statements like [for $myvar]...[endfor]

            We replace the for and endfor statements with the text between them, for each value in the variable.

            :param doc: the document to fill
            :param local_variables: the variables
            :return: None
            """

            def compute_for(doc, local_x_found):
                """
                for one single for statement, cut and paste the content of the for
                :param local_x_found:
                :return:
                """

                def escape_html(s):
                    """
                    Replace special characters "&", "<" and ">" to HTML-safe sequences.
                    If the optional flag quote is true, the quotation mark character (")
                    is also translated.
                    """
                    s = s.replace("&", "&amp;")  # Must be done first!
                    s = s.replace("<", "&lt;")
                    s = s.replace(">", "&gt;")
                    s = s.replace('"', "&quot;")
                    return s

                for_statement = ForStatement(local_x_found.getString())
                foritem_vars = local_variables[for_statement.variable_name]['value']

                # remove the for statement from the odt
                text = local_x_found.getText()
                cursor = text.createTextCursorByRange(local_x_found)
                cursor.goLeft(len(for_statement.for_string), False)
                cursor.goRight(len(for_statement.for_string), True)
                cursor.String = ''

                # select content between for and endfor (including endfor)
                cursor.goRight(1, True)
                selected_string = cursor.String
                match = re.search(ForStatement.end_regex, selected_string, re.IGNORECASE)
                while match is None:
                    cursor.goRight(1, True)
                    selected_string = cursor.String
                    match = re.search(ForStatement.end_regex, selected_string, re.IGNORECASE)

                # remove the endfor from the cursor selection
                cursor.goLeft(len(match.group(0)), True)
                template = cursor.String
                cursor.String = ''
                cursor.goRight(len(match.group(0)), True)
                cursor.String = ''

                # loop on values of the variable
                counter = 0
                for foritem_var in foritem_vars:
                    # search [forindex] and remplace by my counter
                    content = re.sub(ForStatement.forindex_regex, str(counter), template, flags=re.IGNORECASE)

                    # replace inside the selected content selected
                    for match in re.finditer(ForStatement.foritem_regex, content, re.IGNORECASE):
                        # get the variable string
                        var_str = match.group(1)
                        # get the escaping
                        escaping = 'raw'
                        if match.group(2) is not None:
                            escaping = match.group(2)
                        # get separate the var_name by "." to get the value in the dict
                        var_name_hierarchy = var_str.split('.')
                        # get the variable value from the hierarchy
                        value = foritem_var
                        for var_name in var_name_hierarchy:
                            value = value[var_name]
                        # escape the value
                        if escaping == 'escape_html':
                            value = escape_html(value)
                        # replace the variable by its value
                        content = content.replace(match.group(0), value)

                    # paste the content
                    text.insertString(cursor, content, False)

                    # counter increment
                    counter += 1

            # main of for_replace
            search = doc.createSearchDescriptor()
            search.SearchString = ForStatement.start_regex
            search.SearchRegularExpression = True
            search.SearchCaseSensitive = False
            x_found = doc.findFirst(search)
            while x_found is not None:
                compute_for(doc, x_found)
                x_found = doc.findNext(x_found.End, search)

        def if_replace(doc, local_variables: dict[str, dict[str, Union[str, list[str]]]]) -> None:
            """
            Parse statements like [if $myvar==TOTO]...[endif]

            If the condition matches we remove the if and endif statement.
            It the condition doesn't match, we remove the statements and the text between the statements.

            :param doc: the document to fill
            :param local_variables: the variables
            :return: None
            """

            def compute_if(local_x_found):
                """
                Compute the if statement.
                """
                if_statement = IfStatement(local_x_found.getString())
                if_result = if_statement.get_if_result(local_variables[if_statement.variable_name]['value'])
                if not if_result:
                    # le if n'est pas vérifié => on efface le paragraphe avec le if
                    text = local_x_found.getText()
                    cursor = text.createTextCursorByRange(local_x_found)
                    cursor.goLeft(len(if_statement.if_string), False)
                    cursor.goRight(len(if_statement.if_string), True)
                    cursor.goRight(1, True)
                    selected_string = cursor.String
                    match = re.search(IfStatement.end_regex, selected_string, re.IGNORECASE)
                    while match is None:
                        cursor.goRight(1, True)
                        selected_string = cursor.String
                        match = re.search(IfStatement.end_regex, selected_string, re.IGNORECASE)
                    cursor.String = ''
                elif if_result:
                    # the if is verified. We remove the statement and the endif but we keep the content
                    position_in_text = len(if_statement.if_string)
                    text = local_x_found.getText()
                    cursor = text.createTextCursorByRange(local_x_found)
                    cursor.goRight(1, True)
                    position_in_text = position_in_text + 1
                    selected_string = cursor.String
                    match = re.search(IfStatement.end_regex, selected_string, re.IGNORECASE)
                    while match is None:
                        cursor.goRight(1, True)
                        position_in_text += 1
                        selected_string = cursor.String
                        match = re.search(IfStatement.end_regex, selected_string, re.IGNORECASE)
                    cursor.goLeft(len(match.group(0)), False)
                    cursor.goRight(len(match.group(0)), True)
                    position_in_text -= len(match.group(0))
                    cursor.String = ''
                    cursor.goLeft(position_in_text, False)
                    cursor.goRight(len(if_statement.if_string), True)
                    cursor.String = ''

            # main of if_replace
            search = doc.createSearchDescriptor()
            search.SearchString = IfStatement.start_regex
            search.SearchRegularExpression = True
            search.SearchCaseSensitive = False
            x_found = doc.findFirst(search)
            while x_found is not None:
                compute_if(x_found)
                x_found = doc.findNext(x_found.End, search)

        def text_fill(doc, variable: str, value: str) -> None:
            """
            Fills all the text-related content

            :param doc: the document to fill
            :param variable: the variable to search
            :param value: the value to replace with
            :return: None
            """

            search = doc.createSearchDescriptor()
            search.SearchString = variable
            founded = doc.findAll(search)
            instances = [founded.getByIndex(i) for i in range(founded.getCount())]

            for string in instances:
                string.String = string.String.replace(variable, value)

            for page in doc.getDrawPages():
                for shape in page:
                    if shape.getShapeType() == "com.sun.star.drawing.TextShape":
                        shape.String = shape.String.replace(variable, value)

        def image_fill(doc, graphic_provider, variable: str, path: str, should_resize=True) -> None:
            """
            Fills all the image-related content

            :param should_resize: specify if the image should be resized to keep his original size ratio
            :param graphic_provider: the graphic provider, from the established connection
            :param doc: the document to fill
            :param variable: the variable to search
            :param path: the path of the image to replace with
            :return: None
            """

            if not path:
                return

            for graphic_object in doc.getGraphicObjects():
                if graphic_object.LinkDisplayName != variable:
                    continue

                new_image = graphic_provider.queryGraphic((PropertyValue('URL', 0, get_file_url(path), 0),))

                if should_resize:
                    with Image.open(request.urlopen(path) if is_network_based(path) else path) as image:
                        ratio = image.width / image.height
                    new_size = Size()
                    new_size.Height = graphic_object.Size.Height
                    new_size.Width = graphic_object.Size.Height * ratio
                    graphic_object.setSize(new_size)

                graphic_object.Graphic = new_image

        def tables_fill(doc, text_prefix: str, table_prefix: str) -> None:
            """
            Fills all the table-related content

            :param doc: the document to fill
            :param text_prefix: the prefix for text variables
            :param table_prefix: the prefix for table variables
            :return: None
            """

            search = doc.createSearchDescriptor()
            matches = []
            for element, infos in sorted(variables.items(), key=lambda s: -len(s[0])):
                if infos['type'] != 'table':
                    continue
                search.SearchString = (text_prefix if '(' in element else table_prefix) + element
                founded = doc.findAll(search)
                matches += [founded.getByIndex(i) for i in range(founded.getCount()) if founded.getByIndex(i).TextTable]
            tab_vars = [{
                "table": variable.TextTable,
                "var": variable.String
            } for variable in matches]

            tables = [
                {'table': tab, 'vars':
                    {tab_var['var']: variables[tab_var['var'][1:]]['value']
                     for tab_var in tab_vars if tab_var['table'] == tab}
                 } for tab in list(set(variable['table'] for variable in tab_vars))
            ]

            for element in tables:

                table = element['table']
                table_vars = element['vars']
                var_row_pos = len(table.getRows()) - 1
                nb_rows_to_add = max([len(variable) for variable in table_vars.values()])
                table.getRows().insertByIndex(var_row_pos + 1, nb_rows_to_add - 1)
                table_values = table.getDataArray()
                var_row = table_values[var_row_pos]
                static_rows = table_values[:var_row_pos]

                for i in range(nb_rows_to_add):
                    new_row = var_row
                    for variable_name, variable_value in sorted(table_vars.items(), key=lambda s: -len(s[0])):
                        new_row = tuple(
                            elem.replace(
                                variable_name, variable_value[i]
                                if i < len(variable_value) else ""
                            ) for elem in new_row
                        )
                    static_rows += (new_row,)
                table.setDataArray(static_rows)

        if self.new:
            self.new.dispose()
            self.new.close(True)

        try:
            self.new = (self.cnx.desktop.loadComponentFromURL(self.file_url, "_blank", 0, ()))
        except DisposedException as e:
            raise errors.UnoException(
                'bridge_exception',
                f"The connection bridge on '{self.cnx.host}:{self.cnx.port}' crashed on file opening."
                f"Please restart the soffice process. For more informations on what caused this bug and how to "
                f"avoid it, please read the README file, section 'Unsolvable Problems'.",
                dict_of(self.cnx.host, self.cnx.port)
            ) from e
        except RuntimeException as e:
            raise errors.UnoException(
                'connection_closed',
                f"The previously established connection with the soffice process on "
                f"'{self.cnx.host}:{self.cnx.port}' has been closed, or ran into an unknown error. "
                f"Please restart the soffice process, and retry.",
                dict_of(self.cnx.host, self.cnx.port)
            ) from e

        ###
        ### main calls
        ###
        for_replace(self.new, variables)

        if_replace(self.new, variables)

        for var, details in sorted(variables.items(), key=lambda s: -len(s[0])):
            if details['type'] == 'text':
                text_fill(self.new, "$" + var, details['value'])
            elif details['type'] == 'image':
                image_fill(self.new, self.cnx.graphic_provider, "$" + var, details['value'])

        html_replace(self.new)

        tables_fill(self.new, '$', '&')

    def export(self, name: str, should_replace=False) -> Union[str, None]:
        """
        Exports the newly generated document, if any.

        :param should_replace: precise if the exported file should replace the fils with the same name
        :param name: the path/name with file extension of the file to export.
        file type is automatically deducted from it.
        :return: the full path of the exported document, or None if there is no document to export
        """

        if not self.new:
            return

        file_type = name.split(".")[-1]
        path = os.getcwd() + "/" + name if name != '/' else name
        path_without_num = path
        if not should_replace:
            i = 1
            while os.path.isfile(path):
                path = path_without_num[:-(len(file_type) + 1)] + f"_{i}." + file_type
                i += 1

        url = unohelper.systemPathToFileUrl(path)

        # list of available convert filters
        # cf https://help.libreoffice.org/latest/he/text/shared/guide/convertfilters.html
        formats = {
            "odt": "writer8",
            "pdf": "writer_pdf_Export",
            "html": "HTML (StarWriter)",
            "docx": "Office Open XML Text",
            "txt": "Text (encoded)",
            'rtf': 'Rich Text Format'
        }

        try:
            self.new.storeToURL(url, (PropertyValue("FilterName", 0, formats[file_type], 0),))

        except KeyError:
            raise errors.ExportError('invalid_format',
                                     f"Invalid export format {file_type!r}.", dict_of(file_type)) from None
        except IOException as error:
            raise errors.ExportError(
                'unknown_error',
                f"Unable to save document to {path!r} : error {error.value!r}",
                dict_of(path, error)
            ) from error

        return path

    def close(self) -> None:
        """
        close the template

        :return: None
        """

        if not self:
            return
        if self.new:
            self.new.dispose()
            self.new.close(True)
            self.new = None
        if self.doc:
            self.doc.dispose()
            self.doc.close(True)
        try:
            os.remove(self.file_dir + "/.~lock." + self.file_name + "#")
        except FileNotFoundError:
            pass

    def page_break(self) -> None:
        """
        Add a page break to the document

        :return: None
        """

        if not self.new:
            return

        cursor = self.new.Text.createTextCursor()
        cursor.gotoEnd(False)
        cursor.collapseToEnd()
        cursor.BreakType = PAGE_AFTER
        self.new.Text.insertControlCharacter(cursor, PARAGRAPH_BREAK, False)
