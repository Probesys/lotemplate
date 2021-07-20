import os
import json
import sys
import traceback
import configargparse as cparse
import urllib.request

import uno
import unohelper
from com.sun.star.beans import PropertyValue
from com.sun.star.io import IOException
from com.sun.star.lang import DisposedException
from com.sun.star.connection import NoConnectException


class Errors:

    class JsonException(Exception):
        pass

    class TemplateException(Exception):
        pass

    class ExportException(Exception):
        pass

    class TemplateVariableNotInLastRow(TemplateException):
        pass

    class TemplateInvalidFormat(TemplateException):
        pass

    class JsonGenericVariableError(JsonException):
        def __init__(self, diff, _json: dict[str: str, dict[str: str]], _template: dict[str: str, dict[str: str]],
                     message):
            Exception.__init__(self, message)
            self.json = _json
            self.diff = diff
            self.template = _template

    class JsonMissingRequiredVariable(JsonGenericVariableError):
        pass

    class JsonUnknownVariable(JsonGenericVariableError):
        pass

    class JsonIncorrectTabVariables(JsonException):
        pass

    class JsonIncorrectValueType(JsonException):
        pass

    class JsonEmptyValue(JsonException):
        pass

    class JsonUnknownArgument(JsonException):
        pass

    class JsonInvalidArgument(JsonException):
        pass

    class ExportInvalidFormat(ExportException):
        pass

    class UnoException(Exception):
        pass

    class UnoBridgeException(UnoException):
        pass

    class UnoConnectionError(UnoException):
        pass


err = Errors()


class Connexion:

    def __init__(self, host: str, port: str):
        """
        An object representing the connexion between the script and the LibreOffice/OpenOffice processus

        :param host: the address of the host to connect to
        :param port: the host port to connect to
        """

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
                f"run the script."
            ) from e
        self.desktop = self.ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self.ctx)
        self.graphic_provider = self.ctx.ServiceManager.createInstance('com.sun.star.graphic.GraphicProvider')


class Template:

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

        tab_vars_pos = {var.TextTable.Name[1:]:
                        ({text_var.String[1:]: int("".join(filter(str.isdigit, text_var.Cell.CellName)))
                            for text_var in tab_generator if text_var.TextTable.Name == var.TextTable.Name},
                         len(var.TextTable.getRows())) for var in tab_generator}

        for tab_name, tab_infos in tab_vars_pos.items():
            tab_cells = tab_infos[0]
            last_row = tab_infos[1]

            for var_name, var_row in tab_cells.items():
                if var_row != last_row:
                    raise err.TemplateVariableNotInLastRow(
                        f"The variable {repr(var_name)} (table {repr(tab_name)}, file {repr(self.file_url)}) isn't in "
                        f"the last row (got: row {repr(var_row)}, expected: row {repr(last_row)})")

        tab_vars = {var.TextTable.Name[1:]:
                    [{text_var.String[1:]: "" for text_var in tab_generator
                        if text_var.TextTable.Name == var.TextTable.Name}] for var in tab_generator}

        img_vars = {elem[1:]: {"path": ""} for elem in self.doc.getGraphicObjects().getElementNames()
                    if elem[0] == '$'}

        return tab_vars | text_vars | img_vars

    def __init__(self, file_path: str, cnx: Connexion, should_scan: bool):
        """
        An object representing a LibreOffice/OpenOffice template that you can fill, scan, export and more

        :param file_path:
        :param cnx:
        :param should_scan:
        """

        self.cnx = cnx
        self.file_name = file_path
        self.file_url = file_path if is_network_based(file_path) else \
            (unohelper.systemPathToFileUrl(os.path.dirname(os.path.abspath(__file__)) + "/" + file_path if
                                           file_path[0] != '/' else file_path))
        try:
            self.doc = self.cnx.desktop.loadComponentFromURL(self.file_url, "_blank", 0, ())
        except DisposedException as e:
            raise err.UnoBridgeException(
                f"The connection bridge crashed on file opening. Please restart the soffice process. For more "
                f"informations on what caused this bug and how to avoid it, please read the README file, "
                f"section 'Unsolvable Problems'."
            ) from e
        if not self.doc:
            raise err.TemplateInvalidFormat(f"The given format is invalid. (file {repr(self.file_url)})")
        self.variables = self.scan() if should_scan else None
        self.new = None

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
                json_missing[0], json_vars, self.variables,
                f"The value {repr(json_missing[0])}, present in the template {repr(self.file_name)}, isn't present in "
                f"the file {repr(json_name)}"
            )

        template_missing = [key for key in set(json_vars) - set(self.variables)]
        if template_missing:
            raise err.JsonUnknownVariable(
                template_missing[0], json_vars, self.variables,
                f"The variable {repr(template_missing[0])} (file {repr(json_name)}) isn't present in the template "
                f"{repr(self.file_name)}"
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
                f"{repr(self.file_name)}"
            )

        json_missing = [key for key in set(self.variables[bad_key][0]) - set(json_vars[bad_key][0])]
        if json_missing:
            raise err.JsonMissingRequiredVariable(
                json_missing[0], json_vars, self.variables,
                f"The value {repr(json_missing[0])}, present in the template {repr(self.file_name)}, isn't present in "
                f"the table {repr(bad_key)}, file {repr(json_name)}"
            )

        template_missing = [key for key in set(json_vars[bad_key][0]) - set(self.variables[bad_key][0])]
        if template_missing:
            raise err.JsonUnknownVariable(
                template_missing[0], json_vars, self.variables,
                f"The variable {repr(template_missing[0])} (table {repr(bad_key)}, file {repr(json_name)}) "
                f"isn't present in the template {repr(self.file_name)}"
            )

        raise err.JsonGenericVariableError(
            None, json_vars, self.variables,
            f"Variables given in the file {repr(json_name)} don't match with the given "
            f"template {repr(self.file_name)}, but no reason was found"
        )

    def compare_variables(self, given_variables: dict[str: dict[str: str, dict[str: str], list[dict[str: str]]]]) \
            -> dict[str: dict[str: str, list[dict[str: str]]]]:
        """
        Compare all the *args* dictionaries to *self*,
        to verify if all the variables presents in *self* are presents in the given dictionaries, or inversely.
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

        def image_fill(doc, variable: str, value: dict[str: str]) -> None:
            """
            Fills all the image-related content

            :param doc: the document to fill
            :param variable: the variable to search
            :param value: the value to replace with
            :return: None
            """

            # TODO: à coder
            pass

        def table_fill(doc, variable: str, value: list[dict[str: str]]) -> None:
            """
            Fills all the table-related content

            :param doc: the document to fill
            :param variable: the variable to search
            :param value: the value to replace with
            :return: None
            """

            # TODO: à coder
            pass

        if self.new:
            self.new.dispose()
            self.new.close(True)

        try:
            self.new = self.cnx.desktop.loadComponentFromURL(self.file_url, "_blank", 0, ())
        except DisposedException as e:
            raise err.UnoBridgeException(
                f"The connection bridge crashed on file opening. Please restart the soffice process. For more "
                f"informations on what caused this bug and how to avoid it, please read the README file, "
                f"section 'Unsolvable Problems'."
            ) from e

        for variable, value in variables.items():
            
            if isinstance(value, str):
                text_fill(self.new, variable, value)
            elif isinstance(value, list):
                table_fill(self.new, variable, value)
            elif isinstance(value, dict):
                image_fill(self.new, variable, value)

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
        path = os.path.dirname(os.path.abspath(__file__)) + "/" + name if name[0] != '/' else name
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
            raise err.ExportInvalidFormat(f"Invalid export format {repr(file_type)}")
        except IOException as e:
            raise err.ExportException(f"Unable to save document to {repr(path)} : error {e.value}")

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
                raise err.JsonIncorrectValueType(
                    f"The value type {repr(type(value[i]).__name__)} isn't accepted in a table "
                    f"(table {repr(variable)}, file {repr(json_name)}")

            row_cleaned = {}

            for row_key, row_value in value[i].items():
                if type(row_value) != str:
                    raise err.JsonIncorrectValueType(
                        f"The value type {repr(type(row_value).__name__)} isn't accepted in a row "
                        f"(row {repr(i)}, table {repr(variable)}, file {repr(json_name)})")
                row_cleaned[row_key] = ""
            if not row_cleaned:
                raise err.JsonEmptyValue(
                    f"The row n°{repr(i)} is empty (table {repr(variable)}, file {repr(json_name)})")
            cleaned.append(row_cleaned)

        if not cleaned:
            raise err.JsonEmptyValue(f"Table {repr(variable)} is empty (file {repr(json_name)})")

        for i in range(len(cleaned)):
            if cleaned[i] != cleaned[i - 1]:

                missing = [elem for elem in set(cleaned[i - 1]) - set(cleaned[i])]
                if missing:
                    raise err.JsonIncorrectTabVariables(
                        f"The variable {repr(missing[0])}, (row {repr(i if i > 0 else len(cleaned))}, table "
                        f"{repr(variable)}, file {repr(json_name)}), "
                        f"isn't present in the row {repr(i + 1)}"
                    )
                missing = [elem for elem in set(cleaned[i]) - set(cleaned[i - 1])]
                if missing:
                    raise err.JsonIncorrectTabVariables(
                        f"The variable {repr(missing[0])}, (row {repr(i + 1)}, table {repr(variable)}, "
                        f"file {repr(json_name)}), "
                        f"isn't present in the row {repr(i if i > 0 else len(cleaned))}"
                    )

        return [cleaned[0]]

    def get_cleaned_image(json_name: str, variable: str, value: dict) -> dict[str: str]:
        if not value:
            raise err.JsonEmptyValue(f"Image {repr(variable)} is empty (file {repr(json_name)})")
        for image_key, image_value in value.items():
            if image_key != "path":
                raise err.JsonUnknownArgument(
                    f"The argument {repr(image_key)} is not supported in an image (image {repr(variable)}, "
                    f"file {repr(json_name)}")
            if type(image_value) != str:
                raise err.JsonInvalidArgument(
                    f"The argument type {repr(type(image_value).__name__)} is not supported in an image "
                    f"(image {repr(variable)}, file {repr(json_name)})")

        return {"path": ""}

    if type(json_var) is not dict:
        raise err.JsonIncorrectValueType(f"The value type {repr(type(json_var).__name__)} isn't accepted in "
                                         f"json files (file {repr(json_name)})")

    template = {}
    for key, value in json_var.items():
        if type(value) == list:
            value = get_cleaned_table(json_name, key, value)
        elif type(value) == str:
            value = ""
        elif type(value) == dict:
            value = get_cleaned_image(json_name, key, value)
        else:
            raise err.JsonIncorrectValueType(f"The value type {repr(type(value).__name__)} isn't accepted")
        template[key] = value

    return template


def is_network_based(file: str) -> bool:
    """
    Checks if the given file is supposed to be a local file or a network file

    :param file: the file to check
    :return: true if the file is network based, else false
    """

    return bool(file[:8] == "https://" or file[:7] == "http://" or file[:6] == "ftp://" or file[:7] == "file://")


def get_files_json(file_path_list: list[str]) -> dict[str: dict[str: list[dict[str: str]], str, dict[str: str]]]:
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


def set_arguments() -> cparse.Namespace:
    """
    set up all the necessaries arguments, and return them with their values

    :return: user-given values for set up command-line arguments
    """
    import sys

    p = cparse.ArgumentParser(default_config_files=['config.ini'])
    p.add_argument('template_file',
                   help="Template file to scan or fill")
    p.add_argument('--json', '-j', nargs='+', default=sys.stdin,
                   help="Json file(s) that must fill the template, if any")
    p.add_argument('--output', '-o', default="output.pdf",
                   help="Name of the filled file, if the template should be filled. supported formats: "
                        "pdf, html, docx, png, odt")
    p.add_argument('--config', '-c', is_config_file=True, help='Configuration file path')
    p.add_argument('--host', required=True, help='Host address to use for the libreoffice connection')
    p.add_argument('--port', required=True, help='Port to use for the libreoffice connexion')
    p.add_argument('--scan', '-s', action='store_true',
                   help="Specify if the program should just scan the template and return the information, or fill it.")
    p.add_argument('--force_replacement', '-f', action='store_true',
                   help="Specify if the program should ignore the scan's result")
    return p.parse_args()


if __name__ == '__main__':
    """
    before running the script, please run the following command on your OpenOffice host:
    
    soffice "--accept=socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"
    
    read the README file for more infos
    """

    # get the necessaries arguments
    args = set_arguments()

    # establish the connection to the server
    connexion = Connexion(args.host, args.port)

    # generate the document to operate and its parameters
    document = Template(args.template_file, connexion, not args.force_replacement)

    # prints scan result in json format if it should
    if args.scan:
        print(json.dumps(document.variables))

    # fill and export the template if it should
    else:
        vars_list = document.compare_variables(get_files_json(args.json))
        for json_name, json_values in vars_list.items():
            document.fill(json_values)
            print(
                "File " +
                repr(json_name) +
                " : Document saved as " +
                repr(document.export(
                    args.output if len(vars_list) == 1 else
                    ".".join(args.output.split(".")[:-1]) + '_' + json_name.split("/")[-1][:-5] + "." +
                    args.output.split(".")[-1]
                ))
            )
    document.close()
