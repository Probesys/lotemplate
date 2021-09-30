"""
Utils functions, used by the CLI, the API or the core itself
"""


__all__ = ('convert_to_datas_template', 'is_network_based', 'get_file_url',)


import os
import urllib.request
import urllib.error

import unohelper

from .exceptions import err


def convert_to_datas_template(json_name: str, json_var) -> list[dict[str: str, dict[str: list[str]], list[str]]]:
    """
    converts a dictionary of variables for filling a template to a dictionary of variables types,
    like the one returned by self.scan() for comparaison purposes

    :param json_name: the name of the file
    :param json_var: the dictionary to convert
    :return: the converted dictionary
    """

    def get_cleaned_table(table_name: str, table_values: dict) -> dict[str: list[str]]:
        """
        clean a table variable

        :param table_name: the variable name
        :param table_values: the table
        :return: the cleaned table
        """

        if not table_values:
            raise err.JsonEmptyTable(f"Table {repr(table_name)} is empty (file {repr(json_name)}, "
                                     f"instance {repr(index)})",
                                     table_name, json_name, index)

        for variable_name, variable_content in table_values.items():
            if type(variable_content) != list:
                raise err.JsonInvalidTableValueType(
                    f"The value type {repr(type(variable_content).__name__)} isn't accepted in a table "
                    f"(variable {repr(variable_name)}, table {repr(table_name)}, file {repr(json_name)}, "
                    f"instance {repr(index)})",
                    table_name, json_name, index, variable_name, type(variable_content).__name__
                )

            if not variable_content:
                raise err.JsonEmptyTableVariable(
                    f"Variable {repr(variable_name)} is empty (table {repr(table_name)}, file {repr(json_name)}, "
                    f"instance {repr(index)})",
                    table_name, json_name, index, variable_name
                )

            for i, row_value in enumerate(variable_content):
                if type(row_value) != str:
                    raise err.JsonInvalidRowValueType(
                        f"The value type {repr(type(row_value).__name__)} isn't accepted in a row "
                        f"(row {repr(i)}, variable {repr(variable_name)}, table {repr(table_name)}, "
                        f"file {repr(json_name)}, instance {repr(index)})",
                        table_name, json_name, index, variable_name, type(row_value).__name__, i
                    )

        return {variable_name: [""] for variable_name in table_values}

    def get_cleaned_image(image_name: str, image_value: list) -> list[str]:
        """
        clean an image variable

        :param image_name: the variable name
        :param image_value: the image value
        :return: the cleaned image
        """

        if not image_value:
            raise err.JsonImageEmpty(
                f"Image {repr(image_name)} is empty (file {repr(json_name)}, instance {repr(index)})",
                image_name, json_name, index
            )

        if len(image_value) > 1:
            raise err.JsonImageInvalidArgument(
                f"The argument {repr(image_value[1])} should not be present in the image {repr(image_name)} "
                f"(file {repr(json_name)}, instance {repr(index)})",
                image_name, json_name, index, image_value[1]
            )

        if type(image_value[0]) != str:
            raise err.JsonImageInvalidArgumentType(
                f"The argument type {repr(type(image_value[0]).__name__)} is not supported in an image "
                f"(variable 'path', image {repr(image_name)}, file {repr(json_name)}, instance {repr(index)})",
                image_name, json_name, index, image_value[0], type(image_value[0]).__name__
            )

        if not is_network_based(image_value[0]) and not os.path.isfile(image_value[0]):
            raise err.JsonImageInvalidPath(
                f"The file {image_value[0]} don't exist (image {repr(image_name)}, file {repr(json_name)}, "
                f"instance {repr(index)})",
                image_name, json_name, index, image_value[0]
            )
        elif is_network_based(image_value[0]):
            try:
                urllib.request.urlopen(image_value[0])
            except urllib.error.URLError as error:
                raise err.JsonImageInvalidPath(
                    f"The file {image_value[0]} don't exist (image {repr(image_name)}, file {repr(json_name)}, "
                    f"instance {repr(index)})",
                    image_name, json_name, index, image_value[0]
                ) from error

        return [""]

    if type(json_var) is not list:
        raise err.JsonInvalidBaseValueType(
            f"The value type {repr(type(json_var).__name__)} isn't accepted in json files (file {repr(json_name)}), "
            f"only lists",
            json_name, type(json_var).__name__
        )

    if not json_var:
        raise err.JsonEmptyBase(
            f"The given json file is empty (file {repr(json_name)})",
            json_name
        )

    template = []

    for index, elem in enumerate(json_var):

        if type(elem) is not dict:
            raise err.JsonInvalidInstanceValueType(
                f"The value type {repr(type(elem).__name__)} isn't accepted in instance list (file {repr(json_name)}, "
                f"instance {repr(index)}), only dicts",
                json_name, index, type(elem).__name__
            )

        if not elem:
            raise err.JsonEmptyInstance(
                f"The given instance is empty (file {repr(json_name)}, {repr(index)})",
                json_name, index
            )

        inst_template = {}
        for key, value in elem.items():
            if type(value) == dict:
                value = get_cleaned_table(key, value)
            elif type(value) == str:
                value = ""
            elif type(value) == list:
                value = get_cleaned_image(key, value)
            else:
                raise err.JsonInvalidValueType(
                    f"The value type {repr(type(value).__name__)} isn't accepted (variable {repr(key)}, "
                    f"file {repr(json_name)}, instance {repr(index)})",
                    key, json_name, index, type(value).__name__
                )
            inst_template[key] = value
        template.append(inst_template)

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
