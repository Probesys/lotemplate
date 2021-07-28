import os
import json
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


class Errors:
    class JsonException(Exception):
        def __init__(self, message, file):
            self.json_file = file
            super().__init__(message)

    class JsonInvalidBaseValueType(JsonException):
        def __init__(self, message, file, type):
            super().__init__(message, file)
            self.type = type

    class JsonVariableError(JsonException):
        def __init__(self, message, variable: str, _json: str):
            super().__init__(message, _json)
            self.variable = variable

    class JsonImageError(JsonException):
        def __init__(self, message, image: str, _json: str):
            super().__init__(message, _json)
            self.image = image

    class JsonImageEmpty(JsonImageError):
        pass

    class JsonImageInvalidArgument(JsonImageError):
        def __init__(self, message, image: str, _json: str, argument):
            super().__init__(message, image, _json)
            self.argument = argument

    class JsonImageInvalidArgumentType(JsonImageInvalidArgument):
        def __init__(self, message, image: str, _json: str, argument, type):
            super().__init__(message, image, _json, argument)
            self.type = type

    class JsonImageInvalidPath(JsonImageError):
        def __init__(self, message, image, _json, path):
            super().__init__(message, image, _json)
            self.path = path

    class JsonTableError(JsonException):
        def __init__(self, message, table: str, _json: str):
            super().__init__(message, _json)
            self.table = table

    class JsonInvalidTableValueType(JsonTableError):
        def __init__(self, message, table: str, _json: str, type):
            super().__init__(message, table, _json)
            self.type = type

    class JsonInvalidRowValueType(JsonInvalidTableValueType):
        def __init__(self, message, variable: str, _json: str, type, row):
            super().__init__(message, variable, _json, type)
            self.row = row

    class JsonInvalidValueType(JsonVariableError):
        def __init__(self, message, variable: str, _json: str, type):
            super().__init__(message, variable, _json)
            self.type = type

    class JsonEmptyTable(JsonTableError):
        pass

    class JsonEmptyRow(JsonEmptyTable):
        def __init__(self, message, table, json, row):
            super().__init__(message, table, json)
            self.row = row

    class JsonInvalidRowVariable(JsonTableError):
        def __init__(self, message, table, _json, row_present, variable, row_missing):
            super().__init__(message, table, _json)
            self.present_in_row = row_present
            self.missing_in_row = row_missing
            self.variable = variable

    class TemplateException(Exception):
        def __init__(self, message, file):
            super().__init__(message)
            self.file = file

    class TemplateVariableNotInLastRow(TemplateException):
        def __init__(self, message, file, table, row, expected_row, variable):
            super().__init__(message, file)
            self.table = table
            self.actual_row = row
            self.expected_row = expected_row
            self.variable = variable

    class TemplateInvalidFormat(TemplateException):
        def __init__(self, message, template, format):
            super().__init__(message, template)
            self.format = format

    class JsonComparaisonException(Exception):
        def __init__(self, message, json, template):
            self.template_file = template
            self.json_file = json
            super().__init__(message)

    class JsonComparaisonVariableError(JsonComparaisonException):
        def __init__(self, message, variable: str, _json: str, _template: str):
            super().__init__(message, _json, _template)
            self.variable = variable

    class JsonMissingRequiredVariable(JsonComparaisonVariableError):
        pass

    class JsonMissingTableRequiredVariable(JsonMissingRequiredVariable):
        def __init__(self, message, variable: str, _json: str, _template: str, table):
            super().__init__(message, variable, _json, _template)
            self.table = table

    class JsonUnknownVariable(JsonComparaisonVariableError):
        pass

    class JsonIncorrectValueType(JsonComparaisonVariableError):
        def __init__(self, message, variable, json, template, expected_type, actual_type):
            super().__init__(message, variable, json, template)
            self.actual_type = actual_type
            self.expected_type = expected_type

    class JsonUnknownTableVariable(JsonUnknownVariable):
        def __init__(self, message, variable: str, _json: str, _template: str, table):
            super().__init__(message, variable, _json, _template)
            self.table = table

    class ExportException(Exception):
        def __init__(self, message, file):
            super().__init__(message)
            self.file = file

    class ExportInvalidFormat(ExportException):
        def __init__(self, message, file, format):
            super().__init__(message, file)
            self.format = format

    class ExportUnknownError(ExportException):
        def __init__(self, message, file, exception):
            super().__init__(message, file)
            self.exception = exception

    class FileNotFoundError(Exception):
        def __init__(self, message, file):
            super().__init__(message)
            self.file = file

    class UnoException(Exception):
        def __init__(self, message, host, port):
            super().__init__(message)
            self.host = host
            self.port = port

    class UnoBridgeException(UnoException):
        def __init__(self, message, host, port, file):
            super().__init__(message, host, port)
            self.file = file

    class UnoConnectionError(UnoException):
        pass

    class UnoConnectionClosed(UnoConnectionError):
        pass



err = Errors()


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
        print(self.file_url)
        self.variables = self.scan() if should_scan else None
        self.new = None

    def scan(self) -> dict[str: dict, str]:
        """
        scans the variables contained in the template. Supports text, tables and images

        :return: list containing all the variables founded in the template
        """

        search = self.doc.createSearchDescriptor()
        search.SearchRegularExpression = True
        search.SearchString = '\\$[:alnum:]*'
        founded = self.doc.findAll(search)

        var_generator = set(founded.getByIndex(i) for i in range(founded.getCount()))

        text_vars = {var.String[1:]: "" for var in var_generator if
                     not var.TextTable or var.TextTable.Name[0] != "$"}

        if "" in text_vars.keys():
            text_vars.pop("")

        tab_generator = set(var for var in var_generator if var.TextTable and var.TextTable.Name[0] == "$")

        tab_vars_pos = {var.TextTable.Name[1:]: (
            {text_var.String[1:]: int("".join(filter(str.isdigit, text_var.Cell.CellName)))
             for text_var in tab_generator if text_var.TextTable.Name == var.TextTable.Name},
            len(var.TextTable.getRows())
        ) for var in tab_generator}

        for tab_name, tab_infos in tab_vars_pos.items():
            tab_cells = tab_infos[0]
            last_row = tab_infos[1]

            for var_name, var_row in tab_cells.items():
                if var_row != last_row:
                    raise err.TemplateVariableNotInLastRow(
                        f"The variable {repr(var_name)} (table {repr(tab_name)}, file {repr(self.file_name)}) isn't in "
                        f"the last row (got: row {repr(var_row)}, expected: row {repr(last_row)})",
                        self.file_name, tab_name, var_row, last_row, var_name
                    )

        tab_vars = {var.TextTable.Name[1:]: [
            {text_var.String[1:]: "" for text_var in tab_generator if text_var.TextTable.Name == var.TextTable.Name}
        ] for var in tab_generator}

        img_vars = {elem[1:]: {"path": ""} for elem in self.doc.getGraphicObjects().getElementNames()
                    if elem[0] == '$'}

        return tab_vars | text_vars | img_vars

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
            search.SearchString = '$' + variable
            founded = doc.findAll(search)
            instances = [founded.getByIndex(i) for i in range(founded.getCount())]

            for string in instances:
                string.String = string.String.replace('$' + variable, value)

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

            graphic_object = doc.getGraphicObjects().getByName('$' + variable)
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

        def table_fill(doc, variable: str, value: list[dict[str: str]]) -> None:
            """
            Fills all the table-related content

            :param doc: the document to fill
            :param variable: the variable to search
            :param value: the value to replace with
            :return: None
            """

            table = doc.getTextTables().getByName("$" + variable)
            var_row_pos = len(table.getRows()) - 1
            table.getRows().insertByIndex(len(table.getRows()), len(value) - 1)
            tab_values = table.getDataArray()
            var_row = tab_values[var_row_pos]
            static_rows = tab_values[:var_row_pos]
            for row_datas in value:
                new_row = var_row
                for row_variable, row_value in row_datas.items():
                    new_row = tuple(elem.replace('$' + row_variable, row_value) for elem in new_row)
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
                text_fill(self.new, variable, value)
            elif isinstance(value, list):
                table_fill(self.new, variable, value)
            elif isinstance(value, dict):
                image_fill(self.new, self.cnx.graphic_provider, variable, value)

    def export(self, name: str) -> [str, None]:
        """
        Exports the newly generated document, if any.

        :param name: the path/name with file extension of the file to export.
        file type is automatically deducted from it.
        :return: the full path of the exported document, or None if there is no document to export
        """

        if not self.new:
            return

        file_type = name.split(".")[-1]
        path = os.getcwd() + "/" + name if name[0] != '/' else name
        path_without_num = path
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
            "png": "writer_png_Export",
        }

        try:
            self.new.storeToURL(url, (PropertyValue("FilterName", 0, formats[file_type], 0),))

        except KeyError:
            raise err.ExportInvalidFormat(
                f"Invalid export format {repr(file_type)} for file {repr(self.file_name)}",
                self.file_name, file_type
            )
        except IOException as e:
            raise err.ExportUnknownError(
                f"Unable to save document to {repr(path)} : error {e.value}",
                self.file_name, e
            )

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


def convert_to_datas_template(json_name: str, json_var: dict) -> dict[str: str, dict[str: str], list[dict[str: str]]]:
    """
    converts a dictionary of variables for filling a template to a dictionary of variables types,
    like the one returned by self.scan()

    :param json_name: the name of the file
    :param json_var: the dictionary to convert
    :return: the converted dictionary
    """

    def get_cleaned_table(json_name: str, variable: str, value: list) -> list[dict[str: str]]:
        """
        clean a table variable

        :param json_name: the name of the json
        :param variable: the variable name
        :param value: the table
        :return: the cleaned table
        """

        cleaned = []

        for i in range(len(value)):
            if type(value[i]) != dict:
                raise err.JsonInvalidTableValueType(
                    f"The value type {repr(type(value[i]).__name__)} isn't accepted in a table "
                    f"(table {repr(variable)}, file {repr(json_name)}",
                    variable, json_name, type(value[i]).__name__
                )

            row_cleaned = {}

            for row_key, row_value in value[i].items():
                if type(row_value) != str:
                    raise err.JsonInvalidRowValueType(
                        f"The value type {repr(type(row_value).__name__)} isn't accepted in a row "
                        f"(row {repr(i)}, table {repr(variable)}, file {repr(json_name)})",
                        variable, json_name, type(row_value).__name__, i
                    )
                row_cleaned[row_key] = ""
            if not row_cleaned:
                raise err.JsonEmptyRow(
                    f"The row n°{repr(i)} is empty (table {repr(variable)}, file {repr(json_name)})",
                    variable, json_name, i
                )
            cleaned.append(row_cleaned)

        if not cleaned:
            raise err.JsonEmptyTable(f"Table {repr(variable)} is empty (file {repr(json_name)})",
                                     variable, json_name)

        for i in range(len(cleaned)):
            if cleaned[i] != cleaned[i - 1]:

                missing = [elem for elem in set(cleaned[i - 1]) - set(cleaned[i])]
                if missing:
                    raise err.JsonInvalidRowVariable(
                        f"The variable {repr(missing[0])}, (row {repr(i if i > 0 else len(cleaned))}, table "
                        f"{repr(variable)}, file {repr(json_name)}), "
                        f"isn't present in the row {repr(i + 1)}",
                        variable, json_name, i, missing[0], i + 1
                    )
                missing = [elem for elem in set(cleaned[i]) - set(cleaned[i - 1])]
                if missing:
                    raise err.JsonInvalidRowVariable(
                        f"The variable {repr(missing[0])}, (row {repr(i + 1)}, table {repr(variable)}, "
                        f"file {repr(json_name)}), "
                        f"isn't present in the row {repr(i if i > 0 else len(cleaned))}",
                        variable, json_name, i + 1, missing[0], i
                    )

        return [cleaned[0]]

    def get_cleaned_image(json_name: str, variable: str, value: dict) -> dict[str: str]:
        if not value:
            raise err.JsonImageEmpty(
                f"Image {repr(variable)} is empty (file {repr(json_name)})",
                variable, json_name
            )
        for image_key, image_value in value.items():
            if image_key != "path":
                raise err.JsonImageInvalidArgument(
                    f"The argument {repr(image_key)} is not supported in an image (image {repr(variable)}, "
                    f"file {repr(json_name)}",
                    variable, json_name, image_key
                )
            if type(image_value) != str:
                raise err.JsonImageInvalidArgumentType(
                    f"The argument type {repr(type(image_value).__name__)} is not supported in an image "
                    f"(variable 'path', image {repr(variable)}, file {repr(json_name)})",
                    variable, json_name, image_key, type(image_value).__name__
                )

        if not is_network_based(value["path"]) and not os.path.isfile(value["path"]):
            raise err.JsonImageInvalidPath(
                "The file " + value["path"] + f" don't exist (image {repr(variable)}, file {repr(json_name)})",
                variable, json_name, value["path"]
            )
        elif is_network_based(value["path"]):
            try:
                urllib.request.urlopen(value["path"])
            except urllib.error.URLError as error:
                raise err.JsonImageInvalidPath(
                    "The file " + value["path"] + f" don't exist (image {repr(variable)}, file {repr(json_name)})",
                    variable, json_name, value["path"]
                ) from error

        return {"path": ""}

    if type(json_var) is not dict:
        raise err.JsonInvalidBaseValueType(
            f"The value type {repr(type(json_var).__name__)} isn't accepted in json files (file {repr(json_name)}), "
            f"only dictionaries",
            json_name, type(json_var).__name__
        )

    template = {}
    for key, value in json_var.items():
        if type(value) == list:
            value = get_cleaned_table(json_name, key, value)
        elif type(value) == str:
            value = ""
        elif type(value) == dict:
            value = get_cleaned_image(json_name, key, value)
        else:
            raise err.JsonInvalidValueType(
                f"The value type {repr(type(value).__name__)} isn't accepted (variable {repr(key)}, "
                f"file {repr(json_name)})",
                key, json_name, type(value).__name__
            )
        template[key] = value

    return template


def is_network_based(file: str) -> bool:
    """
    Checks if the given file is supposed to be a local file or a network file

    :param file: the file to check
    :return: true if the file is network based, else false
    """

    return bool(file[:8] == "https://" or file[:7] == "http://" or file[:6] == "ftp://" or file[:7] == "file://")


def get_file_url(file: str) -> str:
    return file if is_network_based(file) else (
        unohelper.systemPathToFileUrl(
            os.getcwd() + "/" + file if file[0] != '/' else file
        )
    )


def get_files_json(file_path_list: list[str]) -> dict[str: dict]:
    """
    converts all the specified json files to file_name: dict

    :param file_path_list: the paths of all the json files to convert
    :return: format {file_name: values_dict,...} the converted list of dictionaries
    """

    jsons = {}

    for file_path in file_path_list:
        try:
            if is_network_based(file_path):
                jsons[file_path] = json.loads(urllib.request.urlopen(file_path).read())
            else:
                with open(file_path) as f:
                    jsons[file_path] = json.loads(f.read())
        except Exception as exception:
            print(f'Ignoring exception on file {file_path}', file=sys.stderr)
            traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
            continue

    return jsons


def get_normized_json(json_strings: list[str]) -> dict[str: dict]:
    """
    converts a given list of strings to and code-usable dict of jsons

    :param json_strings: the list of strings to convert to dict
    :return: format {file_name: values_dict,...} the converted list of dictionaries
    """

    jsons = {}

    for i in range(len(json_strings)):
        try:
            jsons["string_n" + str(i + 1)] = json.loads(json_strings[i])
        except Exception as exception:
            print(f'Ignoring exception on json string n°{i + 1}', file=sys.stderr)
            traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    return jsons
