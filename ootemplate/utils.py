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
