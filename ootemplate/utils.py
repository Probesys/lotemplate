"""
Utils functions, used by the CLI, the API or the core itself
"""


__all__ = ('convert_to_datas_template', 'is_network_based', 'get_file_url', 'get_files_json', 'get_normized_json',)


import json
import sys
import traceback
import os
import urllib.request
import urllib.error

import unohelper

from .exceptions import err


def convert_to_datas_template(json_name: str, json_var: dict) -> dict[str: str, dict[str: list[str]], list[str]]:
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
            raise err.JsonEmptyTable(f"Table {repr(table_name)} is empty (file {repr(json_name)})",
                                     table_name, json_name)

        for variable_name, variable_content in table_values.items():
            if type(variable_content) != list:
                raise err.JsonInvalidTableValueType(
                    f"The value type {repr(type(variable_content).__name__)} isn't accepted in a table "
                    f"(variable {repr(variable_name)}, table {repr(table_name)}, file {repr(json_name)}",
                    table_name, json_name, variable_name, type(variable_content).__name__
                )

            if not variable_content:
                raise err.JsonEmptyTableVariable(
                    f"Variable {repr(variable_name)} is empty (table {repr(table_name)}, file {repr(json_name)})",
                    table_name, json_name, variable_name
                )

            for i, row_value in enumerate(variable_content):
                if type(row_value) != str:
                    raise err.JsonInvalidRowValueType(
                        f"The value type {repr(type(row_value).__name__)} isn't accepted in a row "
                        f"(row {repr(i)}, variable {repr(variable_name)}, table {repr(table_name)}, "
                        f"file {repr(json_name)})",
                        table_name, json_name, variable_name, type(row_value).__name__, i
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
                f"Image {repr(image_name)} is empty (file {repr(json_name)})",
                image_name, json_name
            )

        if len(image_value) > 1:
            raise err.JsonImageInvalidArgument(
                f"The argument {repr(image_value[1])} should not be present in the image {repr(image_name)} "
                f"(file {repr(json_name)})",
                image_name, json_name, image_value[1]
            )

        if type(image_value[0]) != str:
            raise err.JsonImageInvalidArgumentType(
                f"The argument type {repr(type(image_value[0]).__name__)} is not supported in an image "
                f"(variable 'path', image {repr(image_name)}, file {repr(json_name)})",
                image_name, json_name, image_value[0], type(image_value[0]).__name__
            )

        if not is_network_based(image_value[0]) and not os.path.isfile(image_value[0]):
            raise err.JsonImageInvalidPath(
                "The file " + image_value[0] + f" don't exist (image {repr(image_name)}, file {repr(json_name)})",
                image_name, json_name, image_value[0]
            )
        elif is_network_based(image_value[0]):
            try:
                urllib.request.urlopen(image_value[0])
            except urllib.error.URLError as error:
                raise err.JsonImageInvalidPath(
                    "The file " + image_value[0] + f" don't exist (image {repr(image_name)}, file {repr(json_name)})",
                    image_name, json_name, image_value[0]
                ) from error

        return [""]

    if type(json_var) is not dict:
        raise err.JsonInvalidBaseValueType(
            f"The value type {repr(type(json_var).__name__)} isn't accepted in json files (file {repr(json_name)}), "
            f"only dictionaries",
            json_name, type(json_var).__name__
        )

    template = {}
    for key, value in json_var.items():
        if type(value) == dict:
            value = get_cleaned_table(key, value)
        elif type(value) == str:
            value = ""
        elif type(value) == list:
            value = get_cleaned_image(key, value)
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
