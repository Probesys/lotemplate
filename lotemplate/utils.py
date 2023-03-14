"""
Copyright (C) 2023 Probesys


Utils functions, used by the CLI, the API or the core itself
"""

__all__ = (
    'convert_to_datas_template',
    'is_network_based',
    'get_file_url',
    'var_regexes'
)

import functools
import os
import types
import urllib.request
import urllib.error
from typing import Union
from sorcery import dict_of
from copy import deepcopy
import regex

from . import errors


def convert_to_datas_template(json) -> dict[dict[str: Union[str, list]]]:
    """
    converts a dictionary of variables for filling a template to a dictionary of variables types,
    like the one returned by self.scan() for comparaison purposes

    :param json: the dictionary to convert
    :return: the converted dictionary
    """

    def get_type(obj, **kargs) -> str:
        """
        Abstract and jsonify the type of the given object - or the given type
        :param obj: the object or type
        :param kargs: the keyword-only arguments
        :Keyword Arguments:
            * *is_type* (``bool``) --
                precise if obj is already a type or not
        :return: the displayable type
        """
        # Unions non prises en charges
        if 'is_type' in kargs and kargs['is_type'] is True:
            pytype = obj
        else:
            pytype = type(obj) if obj is not None else None
        if type(pytype) is type:
            if pytype is dict:
                return "object"
            elif pytype is str:
                return "string"
            elif pytype is bool:
                return "boolean"
            elif pytype is list:
                return "array"
            elif pytype is int:
                return "number"
            else:
                return pytype.__name__
        elif pytype is None:
            return "null"
        elif type(pytype) is types.GenericAlias:
            return get_type(pytype.__origin__, is_type=True) + '[' + ", ".join(
                [get_type(elem, is_type=True) for elem in pytype.__args__]) + ']'

    if type(json) is not dict:
        raise errors.JsonSyntaxError(
            'invalid_base_value_type',
            f"The value type {repr(get_type(json))} isn't accepted in json, only objects",
            dict(variable_type=type(json).__name__)
        )

    def check_type(f):
        """
        A decorator that checks if the arguments are of the right type, following typeints of the function

        :param f: the function to wraps
        :return: the wrapper
        """
        # pris en charge : toutes les objects non récursifs (int, str, bool), None, ainsi que les listes
        # (première instance seulement) et dictionnaires (clé et valeur)
        @functools.wraps(f)
        def wrapper_check_type(var_name, var_value):
            var_type = f.__annotations__['var_value']

            def recursive_check_type(rec_type, rec_value):
                if (type(rec_type) is type and type(rec_value) is not rec_type) or \
                        (rec_type is None and rec_value is not None):
                    raise errors.JsonSyntaxError(
                        'invalid_variable_value_type',
                        f"The variable value type {repr(get_type(rec_value))} isn't accepted for variable type "
                        f"{repr(f.__name__[12:])}, only {repr(get_type(rec_type, is_type=True))} is "
                        f"(variable: {repr(var_name)}).",
                        dict(
                            actual_variable_value_type=get_type(rec_value),
                            expected_variable_value_type=get_type(rec_type, is_type=True),
                            variable_type=f.__name__[12:], variable=var_name
                        )
                    )
                elif type(rec_type) is types.GenericAlias:
                    if type(rec_value) is not rec_type.__origin__:
                        raise errors.JsonSyntaxError(
                            'invalid_variable_value_type',
                            f"The variable value type {repr(get_type(rec_value))} isn't accepted for variable type "
                            f"{repr(f.__name__[12:])}, only {repr(get_type(rec_type, is_type=True))} is "
                            f"(variable: {repr(var_name)}).",
                            dict(
                                actual_variable_value_type=get_type(rec_value),
                                expected_variable_value_type=get_type(rec_type, is_type=True),
                                variable_type=f.__name__[12:], variable=var_name
                            )
                        )
                    try:
                        if not rec_value:
                            raise errors.JsonSyntaxError(
                                'missing_variable_elements',
                                f"The variable {repr(var_name)} is missing some required elements (expected: "
                                f"{repr(get_type(rec_type, is_type=True))}",
                                dict(varible=var_name, expected_variable_value_type=get_type(rec_type, is_type=True))
                            )
                        if rec_type.__origin__ == list:
                            for element in rec_value:
                                recursive_check_type(rec_type.__args__[0], element)
                        if rec_type.__origin__ == dict:
                            for key, value in rec_value:
                                recursive_check_type(rec_type.__args__[0], key)
                                recursive_check_type(rec_type.__args__[1], value)
                    except errors.JsonSyntaxError:
                        raise errors.JsonSyntaxError(
                            'invalid_variable_value_type',
                            f"The variable value type provided in variable {repr(var_name)} isn't accepted for "
                            f"variable type {repr(f.__name__[12:])}, only {repr(get_type(rec_type, is_type=True))} is.",
                            dict(
                                expected_variable_value_type=get_type(rec_type, is_type=True),
                                variable_type=f.__name__[12:], variable=var_name
                            )
                        )
            recursive_check_type(var_type, var_value)
            return f(var_name, var_value)
        return wrapper_check_type

    @check_type
    def get_cleaned_table(var_name: str, var_value: list[str]) -> list[str]:
        """
        clean a table variable
        :param var_name: the variable name
        :param var_value: the table
        :return: the cleaned table
        """
        return [""]

    @check_type
    def get_cleaned_image(var_name: str, var_value: str) -> str:
        """
        clean an image variable

        :param var_name: the variable name
        :param var_value: the image value
        :return: the cleaned image
        """

        if not is_network_based(var_value) and not os.path.isfile(var_value):
            raise errors.JsonSyntaxError(
                'image_invalid_path',
                f"The image {repr(var_value)} doesn't exist (variable {repr(var_name)})",
                dict(variable=var_name, value=var_value)
            )
        elif is_network_based(var_value):
            try:
                urllib.request.urlopen(var_value)
            except urllib.error.URLError as error:
                raise errors.JsonSyntaxError(
                    'image_invalid_path',
                    f"The image {repr(var_value)} doesn't exist (variable {repr(var_name)})",
                    dict(variable=var_name, value=var_value)
                ) from error

        return ""

    @check_type
    def get_cleaned_text(var_name: str, var_value: str) -> str:
        """
        clean a text variable

        :param var_name: the variable name
        :param var_value: the text value
        :return: the cleaned text
        """
        return ""

    json = deepcopy(json)

    template = {}
    for variable_name, variable_infos in json.items():
        if type(variable_infos) != dict:
            raise errors.JsonSyntaxError(
                'invalid_variable_base_value_type',
                f"The value type {repr(get_type(variable_infos))} isn't accepted in variable, only objects "
                f"(variable {repr(variable_name)}).",
                dict_of(variable_name, variable_type=get_type(variable_infos))
            )

        if 'type' not in variable_infos or 'value' not in variable_infos:
            raise errors.JsonSyntaxError(
                'missing_variable_informations',
                f"The information {repr('value' if 'type' in variable_infos else 'type')} is missing from the variable "
                f"{repr(variable_name)}",
                dict_of(variable_name, missing_information=('value' if 'type' in variable_infos else 'type'))
            )

        if invalid_infos := list(set(variable_infos) - {'type', 'value'}):
            raise errors.JsonSyntaxError(
                'unknown_variable_information',
                f"The information {repr(invalid_infos[0])} is invalid for the variable {repr(variable_name)}. "
                f"Only 'type' and 'value' are expected.",
                dict_of(variable_name, information=invalid_infos[0])
            )

        if type(variable_infos['type']) != str:
            raise errors.JsonSyntaxError(
                'invalid_variable_type_value_type',
                f"The 'type' information is supposed to be string, not a {repr(get_type(variable_infos['type']))} "
                f"(variable {repr(variable_name)}).",
                dict_of(variable_name, type_info_type=get_type(variable_infos['type']))
            )

        try:
            variable_infos['value'] = eval(
                f"get_cleaned_{variable_infos['type']}(variable_name, variable_infos['value'])")
        except NameError:
            raise errors.JsonSyntaxError(
                'invalid_variable_type',
                f"The variable type {repr(variable_infos['type'])} isn't accepted (variable {repr(variable_name)}).",
                dict_of(variable_name, variable_type=variable_infos['type'])
            )
        template[variable_name] = variable_infos

    return template


def is_network_based(file: str) -> bool:
    """
    Checks if the given file is supposed to be a local file or a network file

    :param file: the file to check
    :return: true if the file is network based, else false
    """

    return bool(file[:8] == "https://" or file[:7] == "http://" or file[:6] == "ftp://" or file[:7] == "file://")


def get_file_url(file: str) -> str:
    """
    returns the URL or URI of the file, following if it's an url or a path

    :param file: the path or url to the file
    :return: the URL or URI to the path
    """
    return file if is_network_based(file) else (
        "file://" + ((os.getcwd() + "/" + file) if file[0] != '/' else file))


var_regexes = {
    'image': regex.compile(r'\$\w+'),
    'text': regex.compile(
        r'\$(\w+(\(((?:\\.|.)*?)\))?)'),
    'table': regex.compile(
        r'\$\w+'
        r'(?:\((?<arg>(?R)|"[^"]*"|[^$&"\s()][^\s()]*)(?:[+ ](?&arg))*\))?'
        r'|(?<var>&\w+)'),
}
