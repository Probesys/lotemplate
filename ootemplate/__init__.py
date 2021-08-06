"""
OOTemplate Filler
~~~~~~~~~~~~~~~~~

A module for manipulate and fill openoffice writter-like documents with given variables
Contains the two used classes, errors raised and some utils fonctions
"""


__title__ = 'OOTemplate Filler'
__version__ = '1.0'
__all__ = (
    'Connexion',
    'Template',
    'err',
    'convert_to_datas_template',
    'is_network_based',
    'get_file_url',
    'get_files_json',
    'get_normized_json',
)

import os
import sys
import traceback
import urllib.request
import urllib.error
from PIL import Image

import uno
import unohelper
from com.sun.star.beans import PropertyValue
from com.sun.star.io import IOException
from com.sun.star.lang import IllegalArgumentException
from com.sun.star.lang import DisposedException
from com.sun.star.connection import NoConnectException
from com.sun.star.uno import RuntimeException
from com.sun.star.awt import Size

from .exceptions import err
from .utils import *


class Connexion:

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
        except NoConnectException as e:
            raise err.UnoConnectionError(
                f"Couldn't find/connect to the soffice process on \'{host}:{port}\'. "
                f"Make sure the soffice process is correctly running with correct host and port informations. "
                f"Read the README file, section 'Executing the script' for more informations about how to "
                f"run the script.",
                host,
                port
            ) from e
        self.desktop = self.ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self.ctx)
        self.graphic_provider = self.ctx.ServiceManager.createInstance('com.sun.star.graphic.GraphicProvider')

    def restart(self) -> None:
        """
        Restart the connexion to the given host

        :return: None
        """

        self.local_ctx = uno.getComponentContext()
        try:
            self.ctx = self.local_ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", self.local_ctx
            ).resolve(f"uno:socket,host={self.host},port={self.port};urp;StarOffice.ComponentContext")
        except NoConnectException as e:
            raise err.UnoConnectionError(
                f"Couldn't find/connect to the soffice process on \'{self.host}:{self.port}\'. "
                f"Make sure the soffice process is correctly running with correct host and port informations. "
                f"Read the README file, section 'Executing the script' for more informations about how to "
                f"run the script.",
                self.host,
                self.port
            ) from e
        self.desktop = self.ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self.ctx)
        self.graphic_provider = self.ctx.ServiceManager.createInstance('com.sun.star.graphic.GraphicProvider')


class Template:

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        return str(self.file_name)

    def __repr__(self):
        return repr(self.file_url)

    def __len__(self):
        return len(self.variables) if self.variables else 0

    def __getitem__(self, item):
        return self.variables[item] if self.variables else None

    def __init__(self, file_path: str, cnx: Connexion, should_scan: bool):
        """
        An object representing a LibreOffice/OpenOffice template that you can fill, scan, export and more

        :param file_path:
        :param cnx:
        :param should_scan:
        """

        self.cnx = cnx
        self.file_name = file_path.split("/")[-1]
        self.file_path = file_path
        self.file_url = get_file_url(file_path)
        try:
            self.doc = self.cnx.desktop.loadComponentFromURL(self.file_url, "_blank", 0, ())
        except DisposedException as e:
            raise err.UnoBridgeException(
                f"The connection bridge on '{self.cnx.host}:{self.cnx.port}' crashed on file opening "
                f"(file {repr(self.file_name)})."
                f"Please restart the soffice process. For more informations on what caused this bug and how to avoid "
                f"it, please read the README file, section 'Unsolvable Problems'.",
                cnx.host,
                cnx.port,
                self.file_name
            ) from e
        except IllegalArgumentException:
            raise err.FileNotFoundError(
                f"the given file does not exist or has not been found (file {repr(file_path)})",
                file_path
            ) from None
        except RuntimeException as e:
            raise err.UnoConnectionClosed(
                f"The previously etablished connection with the soffice process on '{self.cnx.host}:{self.cnx.port}' "
                f"has been closed, or ran into an unknown error. Please restart the soffice process, and retry.",
                cnx.host,
                cnx.port
            ) from e

        if not self.doc:
            raise err.TemplateInvalidFormat(
                f"The given format ({repr(self.file_name.split('.'))}) is invalid. (file {repr(self.file_name)})",
                self.file_name, self.file_name.split('.')
            )
        self.variables = self.scan() if should_scan else None
        self.new = None

    def scan(self) -> dict[str: dict[str: str], str, list[dict[str: str]]]:
        """
        scans the variables contained in the template. Supports text, tables and images

        :return: list containing all the variables founded in the template
        """

        def scan_text(doc, prefix: str) -> dict[str: str]:
            """
            scan for text in the given doc

            :param doc: the document to scan
            :param prefix: the variables prefix
            :return: the scanned variables
            """

            search = doc.createSearchDescriptor()
            search.SearchRegularExpression = True
            search.SearchString = f'\\{prefix}[:alnum:]+'
            founded = doc.findAll(search)

            var_generator = set(founded.getByIndex(i) for i in range(founded.getCount()))

            return {var.String[len(prefix):]: "" for var in var_generator}

        def scan_table(doc, doc_name: str, prefix: str) -> dict[str: list[str: dict[str: str]]]:
            """
            scan for tables in the given doc

            :param doc: the document to scan
            :param doc_name: the name of the document
            :param prefix: the variables prefix
            :return: the scanned variables
            """

            search = doc.createSearchDescriptor()
            search.SearchRegularExpression = True
            search.SearchString = f'\\{prefix}[:alnum:]+'
            founded = doc.findAll(search)

            tab_generator = set(founded.getByIndex(i) for i in range(founded.getCount())
                                if founded.getByIndex(i).TextTable)

            tab_vars_pos = {var.TextTable.Name: (
                {text_var.String[len(prefix):]: int("".join(filter(str.isdigit, text_var.Cell.CellName)))
                 for text_var in tab_generator if text_var.TextTable.Name == var.TextTable.Name},
                len(var.TextTable.getRows())
            ) for var in tab_generator}

            for tab_name, tab_infos in tab_vars_pos.items():
                tab_cells = tab_infos[0]
                last_row = tab_infos[1]

                for var_name, var_row in tab_cells.items():
                    if var_row != last_row:
                        raise err.TemplateVariableNotInLastRow(
                            f"The variable {repr(var_name)} (table {repr(tab_name)}, file {repr(doc_name)}) "
                            f"isn't in the last row (got: row {repr(var_row)}, expected: row {repr(last_row)})",
                            doc_name, tab_name, var_row, last_row, var_name
                        )

            return {
                var.TextTable.Name: [{
                    text_var.String[1:]:
                        "" for text_var in tab_generator if text_var.TextTable.Name == var.TextTable.Name
                }] for var in tab_generator
            }

        def scan_image(doc, prefix: str) -> dict[str: dict[str: str]]:
            """
            scan for images in the given doc

            :param doc: the document to scan
            :param prefix: the variables prefix
            :return: the scanned variables
            """

            return {elem[len(prefix):]: {"path": ""} for elem in doc.getGraphicObjects().getElementNames()
                    if elem[:len(prefix)] == prefix}

        return scan_text(self.doc, "$") | scan_table(self.doc, self.file_name, "&") | scan_image(self.doc, "$")

    def search_error(self, json_vars: dict[str: str, dict[str: str], list[dict[str: str]]], json_name: str) -> None:
        """
        find out which variable is a problem, and raise the required error

        :param json_name: the name of the json file where the error is
        :param json_vars: the given json variables
        :return: None
        """

        if json_vars == self.variables:
            return

        def get_printable_value_type(var) -> str:
            """
            returns the value type of the variable within the document, not the pythonic type

            :param var: the variable whose type is to be retrieved
            :return: a printable value type, following the variable representations
            """

            if type(var) == str:
                return "text"
            elif type(var) == list:
                return "table"
            elif type(var) == dict:
                return "image"
            else:
                return type(var).__name__

        json_missing = [key for key in set(self.variables) - set(json_vars)]
        if json_missing:
            raise err.JsonMissingRequiredVariable(
                f"The value {repr(json_missing[0])}, present in the template {repr(self.file_name)}, isn't present in "
                f"the file {repr(json_name)}",
                json_missing[0], json_name, self.file_name
            )

        template_missing = [key for key in set(json_vars) - set(self.variables)]
        if template_missing:
            raise err.JsonUnknownVariable(
                f"The variable {repr(template_missing[0])} (file {repr(json_name)}) isn't present in the template "
                f"{repr(self.file_name)}",
                template_missing[0], json_name, self.file_name
            )

        json_incorrect = {key: json_vars[key] for key in json_vars if json_vars[key] != self.variables[key]}
        bad_keys = list(json_incorrect.keys())
        bad_keys.sort()
        bad_key = bad_keys[0]

        if type(json_incorrect[bad_key]) is not type(self.variables[bad_key]):
            raise err.JsonIncorrectValueType(
                f"The variable {repr(bad_key)} (file {repr(json_name)}) should be of type "
                f"{repr(get_printable_value_type(self.variables[bad_key]))}, but is of type "
                f"{repr(get_printable_value_type(json_incorrect[bad_key]))}, like in the template "
                f"{repr(self.file_name)}", bad_key, json_name, self.file_name,
                get_printable_value_type(self.variables[bad_key]),
                get_printable_value_type(json_incorrect[bad_key])
            )

        json_missing = [key for key in set(self.variables[bad_key][0]) - set(json_vars[bad_key][0])]
        if json_missing:
            raise err.JsonMissingTableRequiredVariable(
                f"The value {repr(json_missing[0])}, present in the template {repr(self.file_name)}, isn't present in "
                f"the table {repr(bad_key)}, file {repr(json_name)}",
                json_missing[0], json_name, self.file_name, bad_key
            )

        template_missing = [key for key in set(json_vars[bad_key][0]) - set(self.variables[bad_key][0])]
        if template_missing:
            raise err.JsonUnknownTableVariable(
                f"The variable {repr(template_missing[0])} (table {repr(bad_key)}, file {repr(json_name)}) "
                f"isn't present in the template {repr(self.file_name)}",
                template_missing[0], json_name, self.file_name, bad_key
            )

        raise err.JsonComparaisonException(
            f"Variables given in the file {repr(json_name)} don't match with the given "
            f"template {repr(self.file_name)}, but no reason was found",
            json_name, self.file_name
        )

    def compare_variables(self, given_variables: dict[str: dict[str: str, dict[str: str], list[dict[str: str]]]]) \
            -> dict[str: dict[str: str, list[dict[str: str]]]]:
        """
        Compare all the variables in the given dict to *self*,
        to verify if all the variables presents in *self* are presents in the given dictionary, or inversely.
        If not, raise an error

        :param given_variables: format {file_name: values_dict,...} the dicts to compare to the founded
        template-variables
        :return: None
        """

        valid_variables = {}

        for file, json_dict in given_variables.items():
            try:
                json_variables = convert_to_datas_template(file, json_dict)

                self.search_error(json_variables, file)
                valid_variables[file] = json_dict
            except Exception as exception:
                print(f'Ignoring exception on file {file}', file=sys.stderr)
                traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
                continue

        return valid_variables

    def fill(self, variables: dict[str: str, list[dict[str: str]], dict[str: str]]) -> None:
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

        def image_fill(doc, graphic_provider, variable: str, value: dict[str: str], should_resize=True) -> None:
            """
            Fills all the image-related content

            :param should_resize: specify if the image should be resized to keep his original size ratio
            :param graphic_provider: the graphic provider, from the established connection
            :param doc: the document to fill
            :param variable: the variable to search
            :param value: the value to replace with
            :return: None
            """

            graphic_object = doc.getGraphicObjects().getByName(variable)
            path = value['path']
            new_image = graphic_provider.queryGraphic((PropertyValue('URL', 0, get_file_url(path), 0),))

            if should_resize:
                with Image.open(urllib.request.urlopen(path) if is_network_based(path) else path) as image:
                    ratio = image.width / image.height
                new_size = Size()
                new_size.Height = graphic_object.Size.Height
                new_size.Width = graphic_object.Size.Height * ratio
                graphic_object.setSize(new_size)

            graphic_object.Graphic = new_image

        def table_fill(doc, prefix: str, variable: str, value: list[dict[str: str]]) -> None:
            """
            Fills all the table-related content

            :param prefix: the variables prefix
            :param doc: the document to fill
            :param variable: the variable to search
            :param value: the value to replace with
            :return: None
            """

            table = doc.getTextTables().getByName(variable)
            var_row_pos = len(table.getRows()) - 1
            table.getRows().insertByIndex(len(table.getRows()), len(value) - 1)
            tab_values = table.getDataArray()
            var_row = tab_values[var_row_pos]
            static_rows = tab_values[:var_row_pos]
            for row_datas in value:
                new_row = var_row
                for row_variable, row_value in row_datas.items():
                    new_row = tuple(elem.replace(prefix + row_variable, row_value) for elem in new_row)
                static_rows += (new_row,)
            table.setDataArray(static_rows)

        if self.new:
            self.new.dispose()
            self.new.close(True)

        try:
            self.new = self.cnx.desktop.loadComponentFromURL(self.file_url, "_blank", 0, ())
        except DisposedException as e:
            raise err.UnoBridgeException(
                f"The connection bridge on '{self.cnx.host}:{self.cnx.port}' crashed on file opening "
                f"(file {repr(self.file_url)})."
                f"Please restart the soffice process. For more informations on what caused this bug and how to avoid "
                f"it, please read the README file, section 'Unsolvable Problems'.",
                self.cnx.host,
                self.cnx.port,
                self.file_url
            ) from e
        except RuntimeException as e:
            raise err.UnoConnectionClosed(
                f"The previously etablished connection with the soffice process on '{self.cnx.host}:{self.cnx.port}' "
                f"has been closed, or ran into an unknown error. Please restart the soffice process, and retry."
                f"it, please read the README file, section 'Unsolvable Problems'.",
                self.cnx.host,
                self.cnx.port
            ) from e

        for variable, value in variables.items():

            if isinstance(value, str):
                text_fill(self.new, "$" + variable, value)
            elif isinstance(value, list):
                table_fill(self.new, "&", variable, value)
            elif isinstance(value, dict):
                image_fill(self.new, self.cnx.graphic_provider, "$" + variable, value)

    def export(self, name: str, should_replace=False) -> [str, None]:
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
        path = os.getcwd() + "/" + name if name[0] != '/' else name
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
            raise err.ExportInvalidFormat(
                f"Invalid export format {repr(file_type)} for file {repr(self.file_name)}",
                self.file_name, file_type
            ) from None
        except IOException as e:
            raise err.ExportUnknownError(
                f"Unable to save document to {repr(path)} : error {e.value}",
                self.file_name, e
            ) from e

        return path

    def close(self) -> None:
        """
        close the template

        :return: None
        """
        if self.new:
            self.new.dispose()
            self.new.close(True)
        self.doc.dispose()
        self.doc.close(True)
