import io
import json
import configargparse as cparse

import uno
import unohelper


class Connexion:

    def __init__(self, host: str, port: str):
        """
        An object representing the connexion between the script and the LibreOffice/OpenOffice processus

        :param host: the address of the host to connect to
        :param port: the host port to connect to
        """

        self.local_ctx = uno.getComponentContext()
        self.ctx = self.local_ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", self.local_ctx
        ).resolve("uno:socket,host=%s,port=%s;urp;StarOffice.ComponentContext" % (host, port))
        self.desktop = self.ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self.ctx)
        self.graphic_provider = self.ctx.ServiceManager.createInstance('com.sun.star.graphic.GraphicProvider')


class Template:
    class JsonException(Exception):
        pass

    class TemplateException(Exception):
        pass

    def scan(self) -> dict[str: dict, str]:
        """
        scans the variables contained in the template. Supports text, tables and images

        :return: list containing all the variables founded in the template
        """

        class TemplateVariableNotInLastRow(Template.TemplateException):
            pass

        search = self.doc.createSearchDescriptor()
        search.SearchRegularExpression = True
        search.SearchString = '\\$[:alnum:]*'
        founded = self.doc.findAll(search)

        var_generator = set(founded.getByIndex(i) for i in range(founded.getCount()))

        text_vars = {var.String[1:]: None for var in var_generator if
                     not var.TextTable or var.TextTable.Name[0] != "$"}

        if "" in text_vars.keys():
            text_vars.pop("")

        tab_generator = set(var for var in var_generator if var.TextTable and var.TextTable.Name[0] == "$")

        tab_vars_pos = {var.TextTable.Name[1:]: ({text_var.String[1:]: int(text_var.Cell.CellName[1]) for text_var in
                                                  tab_generator if text_var.TextTable.Name == var.TextTable.Name},
                                                 len(var.TextTable.getRows()))
                        for var in tab_generator}

        for tab_name, tab_infos in tab_vars_pos.items():
            tab_cells = tab_infos[0]
            last_row = tab_infos[1]

            for var_name, var_row in tab_cells.items():
                if var_row != last_row:
                    raise TemplateVariableNotInLastRow(
                        f"The variable {repr(var_name)} (table {repr(tab_name)}) isn't in the last row "
                        f"(got: row {repr(var_row)}, expected: row {repr(last_row)})")

        tab_vars = {var.TextTable.Name[1:]: {text_var.String[1:]: None for text_var in tab_generator
                                             if text_var.TextTable.Name == var.TextTable.Name} for var in tab_generator}

        img_vars = {elem[1:]: {"path": None} for elem in self.doc.getGraphicObjects().getElementNames()
                    if elem[0] == '$'}

        return tab_vars | text_vars | img_vars

    def __init__(self, file_path: str, cnx: Connexion, should_scan: bool):
        """
        An object representing a LibreOffice/OpenOffice template that you can fill, scan, export and more

        :param file_path:
        :param cnx:
        :param should_scan:
        """
        import os

        self.cnx = cnx
        self.file_url = unohelper.systemPathToFileUrl(os.path.dirname(os.path.abspath(__file__)) + "/" + file_path)
        self.doc = self.cnx.desktop.loadComponentFromURL(self.file_url, "_blank", 0, ())
        self.variables = self.scan() if should_scan else None

    def compare_variables(self, given_variables: dict[str: dict[str: str, list[dict[str: str]]]]) -> None:
        """
        Compare all the *args* dictionaries to *self*,
        to verify if all the variables presents in *self* are presents in the given dictionaries, or inversely.
        If not, raise an error

        :param given_variables: format {file_name: values_dict,...} the dicts to compare to the founded
        template-variables
        :return: None
        """

        if not self.variables:
            return

        class JsonGenericVariableError(Template.JsonException):
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

        class JsonIncorrectTabVariables(Template.JsonException):
            pass

        class JsonIncorrectValueType(Template.JsonException):
            pass

        class JsonEmptyValue(Template.JsonException):
            pass

        class JsonUnknownArgument(Template.JsonException):
            pass

        class JsonInvalidArgument(Template.JsonException):
            pass

        def convert_to_datas_template(
                json_name, json_var: dict[str: str, list[dict[str: str]]]) -> dict[str: str, dict[str: str]]:
            """
            converts a dictionary of variables for filling a template to a dictionary of variables types,
            like the one returned by self.scan()

            :param json_name: the name of the file
            :param json_var: the dictionary to convert
            :return: the converted dictionary
            """

            template = {}
            for key, value in json_var.items():
                if type(value) == list:

                    cleaned = []

                    for i in range(len(value)):
                        if type(value[i]) != dict:
                            raise JsonIncorrectValueType(
                                f"The value type {repr(type(value[i]).__name__)} isn't accepted in a table "
                                f"(table {repr(key)}, file {repr(json_name)}")

                        row_cleaned = {}

                        for row_key, row_value in value[i].items():
                            if type(row_value) != str:
                                raise JsonIncorrectValueType(
                                    f"The value type {repr(type(row_value).__name__)} isn't accepted in a row "
                                    f"(row {repr(i)}, table {repr(key)}, file {repr(json_name)})")
                            row_cleaned[row_key] = None
                        if not row_cleaned:
                            raise JsonEmptyValue(
                                f"Row n°{repr(i)} is empty (table {repr(key)}, file {repr(json_name)})")
                        cleaned.append(row_cleaned)

                    if not cleaned:
                        raise JsonEmptyValue(f"Table {repr(key)} is empty (file {repr(json_name)})")

                    for i in range(len(cleaned)):
                        if cleaned[i] != cleaned[i - 1]:

                            try:
                                search_error(cleaned[i], cleaned[i - 1], key)
                            except JsonUnknownVariable as err:
                                raise JsonIncorrectTabVariables(
                                    f"The variable {repr(err.diff)}, (row {repr(i if i > 0 else len(cleaned))}, table "
                                    f"{repr(key)}, file {repr(json_name)}), "
                                    f"isn't present in the row {repr(i + 1)}") from None
                            except JsonMissingRequiredVariable as err:
                                raise JsonIncorrectTabVariables(
                                    f"The variable {repr(err.diff)}, (row {repr(i + 1)}, table {repr(key)}, "
                                    f"file {repr(json_name)}), "
                                    f"isn't present in the row {repr(i if i > 0 else len(cleaned))}") from None

                    value = cleaned[0]

                elif type(value) == str:
                    value = None

                elif type(value) == dict:
                    if not value:
                        raise JsonEmptyValue(f"Image {repr(key)} is empty (file {repr(json_name)})")
                    for image_key, image_value in value.items():
                        if image_key != "path":
                            raise JsonUnknownArgument(
                                f"The argument {repr(image_key)} is not supported in an image (image {repr(key)}, "
                                f"file {repr(json_name)}")
                        if type(image_value) != str:
                            raise JsonInvalidArgument(
                                f"The argument type {repr(type(image_value).__name__)} is not supported in an image "
                                f"(image {repr(key)}, file {repr(json_name)})")

                    value = {"path": None}

                else:
                    raise JsonIncorrectValueType(f"The value type {repr(type(value).__name__)} isn't accepted")
                template[key] = value
            return template

        def search_error(template_vars: dict[str: str, dict[str: str]],
                         json_vars: dict[str: str, dict[str: str]],
                         file_name: str) -> None:
            """
            find out which variable is a problem, and raise the required error

            :param file_name: the name of the file where the error is
            :param template_vars: the template variables
            :param json_vars: the given json variables
            :return: None
            """

            json_missing = [key for key in set(template_vars) - set(json_vars)]
            if json_missing:
                raise JsonMissingRequiredVariable(
                    json_missing[0], json_vars, template_vars,
                    f"The required value {repr(json_missing[0])} isn't present in the file {repr(file_name)}")

            template_missing = [key for key in set(json_vars) - set(template_vars)]
            if template_missing:
                raise JsonUnknownVariable(
                    template_missing[0], json_vars, template_vars,
                    f"The variable {repr(template_missing[0])} (file {repr(file_name)}) isn't present in the template")

            json_incorrect = {key: json_vars[key] for key in json_vars if json_vars[key] != template_vars[key]}
            bad_keys = list(json_incorrect.keys())
            bad_keys.sort()
            bad_key = bad_keys[0]
            print(bad_key)
            print(json_incorrect[bad_key])
            print(template_vars[bad_key])

            def get_printable_value_type(var) -> str:
                """
                returns the value type of the variable within the document, not the pythonic type

                :param var: the variable whose type is to be retrieved
                :return: a printable value type, following the variable representations
                """

                if type(var) == type(None):
                    return "text"
                elif type(var) == list:
                    return "table"
                elif type(var) == dict:
                    return "image"
                else:
                    return type(var).__name__

            if not isinstance(type(json_incorrect[bad_key]), type(template_vars[bad_key])):
                raise JsonIncorrectValueType(
                    f"The variable {repr(bad_key)} (file {repr(file_name)}) should be of type "
                    f"{repr(get_printable_value_type(template_vars[bad_key]))}, but is of type "
                    f"{repr(get_printable_value_type(json_incorrect[bad_key]))}")

            json_missing = [key for key in set(template_vars[bad_key]) - set(json_vars[bad_key])]
            if json_missing:
                raise JsonMissingRequiredVariable(
                    json_missing[0], json_vars, template_vars,
                    f"The required value {repr(json_missing[0])} isn't present in the table {repr(bad_key)}, "
                    f"file {repr(file_name)}")

            template_missing = [key for key in set(json_vars[bad_key]) - set(template_vars[bad_key])]
            if template_missing:
                raise JsonUnknownVariable(
                    template_missing[0], json_vars, template_vars,
                    f"The variable {repr(template_missing[0])} (table {repr(bad_key)}, file {repr(file_name)}) "
                    f"isn't present in the template")

            raise JsonGenericVariableError(
                None, json_vars, template_vars,
                f"Variables given in the file {repr(file_name)} don't match with the given "
                "template, but no reason was found")

        for file, json_dict in given_variables.items():
            json_variables = convert_to_datas_template(file, json_dict)

            if not json_variables == self.variables:
                search_error(self.variables, json_variables, str(file))

    def fill(self, given_variables: dict[str: dict[str: str, list[dict[str: str]]]]) -> None:
        self.compare_variables(given_variables)

        # TODO: à coder

    def export(self, name: str) -> None:
        # TODO: à coder
        return


def get_files_json(files: list[io.TextIOWrapper]) -> dict[str: dict[str: list[dict[str: str]], str]]:
    """
    converts all the specified json files to file_name: dict

    :param files: the paths of all the json files to convert
    :return: format {file_name: values_dict,...} the converted list of dictionaries
    """

    jsons = {f.name: json.loads(f.read()) for f in files}
    for f in files:
        f.close()
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
    p.add_argument('--json', '-j', nargs='+', default=sys.stdin, type=cparse.FileType('r'),
                   help="Json file(s) that must fill the template, if any")
    p.add_argument('--output', '-o', default="output.odt",
                   help="Name of the filled file, if the template should be filled")
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
        document.fill(get_files_json(args.json))
        document.export(args.output)
