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
import unohelper
from com.sun.star.beans import PropertyValue, UnknownPropertyException
from com.sun.star.io import IOException
from com.sun.star.lang import IllegalArgumentException, DisposedException
from com.sun.star.connection import NoConnectException
from com.sun.star.uno import RuntimeException
from com.sun.star.awt import Size

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
                f"The previously etablished connection with the soffice process on '{self.cnx.host}:{self.cnx.port}' "
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

    def scan(self, **kargs) -> dict[str: dict[str, Union[str, list[str]]]]:
        """
        scans the variables contained in the template. Supports text, tables and images

        :return: list containing all the variables founded in the template
        """

        should_close = kargs["should_close"] if "should_close" in kargs else False

        def scan_text(doc) -> dict[str, dict[str, str]]:
            """
            scan for text in the given doc

            :param doc: the document to scan
            :return: the scanned variables
            """

            raw_string = doc.getText().getString()

            matches = var_regexes['text'].finditer(raw_string)
            plain_vars = {
                var[0][1:]: {'type': 'text', 'value': ''} for var in matches}

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

            return plain_vars | text_fields_vars

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
        tables = scan_table(self.doc)
        images = scan_image(self.doc)

        variables_list = list(texts.keys()) + list(tables.keys()) + list(images.keys())
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

        return texts | tables | images

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
                f"The previously etablished connection with the soffice process on "
                f"'{self.cnx.host}:{self.cnx.port}' has been closed, or ran into an unknown error. "
                f"Please restart the soffice process, and retry.",
                dict_of(self.cnx.host, self.cnx.port)
            ) from e

        for var, details in sorted(variables.items(), key=lambda s: -len(s[0])):
            if details['type'] == 'text':
                text_fill(self.new, "$" + var, details['value'])
            elif details['type'] == 'image':
                image_fill(self.new, self.cnx.graphic_provider, "$" + var, details['value'])
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
        formats = {
            "odt": "writer8",
            "pdf": "writer_pdf_Export",
            "html": "HTML (StarWriter)",
            "docx": "Office Open XML Text",
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
