"""
Copyright (C) 2023 Probesys
"""

from flask import *

import lotemplate as ot

import configargparse as cparse
import glob
import os
import subprocess
from time import sleep
from typing import Union
from zipfile import ZipFile

p = cparse.ArgumentParser(default_config_files=['config.yml', 'config.ini', 'config'])
p.add_argument('--config', '-c', is_config_file=True, help='Configuration file path')
p.add_argument('--host', default="localhost", help='Host address to use for the libreoffice connection')
p.add_argument('--port', default="2002", help='Port to use for the libreoffice connexion')
args = p.parse_known_args()[0]

os.makedirs("uploads", exist_ok=True)
os.makedirs("exports", exist_ok=True)
subprocess.call(
    f'soffice "--accept=socket,host={args.host},port={args.port};urp;StarOffice.ServiceManager" &', shell=True)
sleep(3)
cnx = ot.Connexion(args.host, args.port)


def restart_soffice() -> None:
    """
    simply restart the soffice process

    :return: None
    """

    clean_temp_files()
    subprocess.call(
        f'soffice "--accept=socket,host={cnx.host},port={cnx.port};urp;StarOffice.ServiceManager" &',
        shell=True
    )
    sleep(2)
    try:
        cnx.restart()
    except:
        pass


def clean_temp_files():
    """
    Deletes all the temporary files created

    :return: None
    """
    for d in os.listdir("uploads"):
        for f in glob.glob(f"uploads/{d}/.~lock.*#"):
            try:
                os.remove(f)
            except FileNotFoundError:
                continue
    for f in os.scandir("exports"):
        try:
            os.remove(f.path)
        except FileNotFoundError:
            continue


def delete_file(directory: str, name: str) -> None:
    """
    Deletes the given file and the temp files created by soffice
    :param directory: the directory containing the file to delete
    :param name: the file to delete
    :return: None
    """

    try:
        os.remove(f"uploads/{directory}/{name}")
    except FileNotFoundError:
        pass
    try:
        os.remove(f"uploads/{directory}/.~lock.{name}#")
    except FileNotFoundError:
        pass


def error_format(exception: Exception, message: str = None) -> dict:
    """
    put all information about an error in a dictionary for better error handling when using the API.
    You can also overwrite the provided error message

    :param exception: the exception to format
    :param message: the message with which it should replace the provided error message
    :return: the formatted dictionary
    """

    formatted = (
        {
            'error': type(exception).__name__,
            'code': exception.code if isinstance(exception, ot.errors.LotemplateError) else type(exception).__name__,
            'message': message or str(exception),
            'variables': exception.infos if isinstance(exception, ot.errors.LotemplateError) else {}
        }
    )
    return formatted


def error_sim(exception: str, code: str, message: str, variables=dict({})) -> dict:
    """
    Simulate an error catch, and return an error-formatted dict in the same way as error_format does

    :param exception: the exception name
    :param code: the exception id
    :param message: the message of the exception
    :param variables: the list of variables to join
    :return: the formatted dict
    """

    return {'error': exception, 'code': code, 'message': message, 'variables': variables}


def save_file(directory: str, f, name: str, error_caught=False) -> Union[tuple[dict, int], dict]:
    """
    upload a template file, and scan it.

    :param f: the file to save
    :param directory: the directory of the file
    :param name: the name of the file
    :param error_caught: specify if an error has been caught
    :return: a json, with the filename under which it was saved (key 'file'),
    and the scanned variables present in the template (key 'variables')
    """

    try:
        os.mkdir(f"uploads/{directory}")
    except FileExistsError:
        pass
    file_type = name.split(".")[-1]
    name_without_num = name
    i = 1
    while os.path.isfile(f"uploads/{directory}/{name}"):
        name = name_without_num[:-(len(file_type) + 1)] + f"_{i}." + file_type
        i += 1
    f.stream.seek(0)
    f.save(f"uploads/{directory}/{name}")
    try:
        with ot.Template(f"uploads/{directory}/{name}", cnx, True) as temp:
            values = temp.variables
    except ot.errors.TemplateError as e:
        delete_file(directory, name)
        return error_format(e), 415
    except ot.errors.UnoException as e:
        delete_file(directory, name)
        restart_soffice()
        if error_caught:
            return (
                error_format(e, "Internal server error on file opening. Please checks the README file, section "
                                "'Unsolvable problems' for more informations."),
                500
            )
        else:
            return save_file(directory, f, name, True)
    except Exception as e:
        delete_file(directory, name)
        return error_format(e), 500
    return {'file': name, 'message': "Successfully uploaded", 'variables': values}


def scan_file(directory: str, file: str, error_caught=False) -> Union[tuple[dict, int], dict]:
    """
    scans the specified file

    :param directory: the directory where the file is
    :param file: the file to scan
    :param error_caught: specify if an error was already caught
    :return: a json and optionally an int which represent the status code to return
    """

    try:
        with ot.Template(f"uploads/{directory}/{file}", cnx, True) as temp:
            variables = temp.variables
    except ot.errors.UnoException as e:
        restart_soffice()
        if error_caught:
            return (
                error_format(e, "Internal server error on file opening. Please checks the README file, section "
                                "'Unsolvable problems' for more informations."),
                500
            )
        else:
            return scan_file(directory, file, True)
    return {'file': file, 'message': "Successfully scanned", 'variables': variables}


def fill_file(directory: str, file: str, json, error_caught=False) -> Union[tuple[dict, int], dict, Response]:
    """
    fill the specified file

    :param directory: the directory where the file is
    :param file: the file to fill
    :param json: the json to fill the document with
    :param error_caught: specify if an error was already caught
    :return: a json and optionally an int which represent the status code to return
    """

    if type(json) != list or not json:
        return error_sim("JsonSyntaxError", 'api_invalid_base_value_type', "The json should be a non-empty array"), 415

    try:
        with ot.Template(f"uploads/{directory}/{file}", cnx, True) as temp:

            exports = []

            for elem in json:

                if (type(elem) != dict or not elem.get("name") or not elem["name"] or type(elem["name"]) != str or
                        elem.get("variables") is None or len(elem) > 2):
                    return error_sim(
                        "JsonSyntaxError",
                        'api_invalid_instance_syntax',
                        "Each instance of the array in the json should be an object containing only 'name' - "
                        "a non-empty string, and 'variables' - a non-empty object"), 415

                try:
                    json_variables = ot.convert_to_datas_template(elem["variables"])
                    temp.search_error(json_variables)
                    temp.fill(elem["variables"])
                    exports.append(temp.export("exports/" + elem["name"], should_replace=(
                        True if len(json) == 1 else False)))
                except Exception as e:
                    return error_format(e), 415

            if len(exports) == 1:
                return send_file(exports[0], download_name=exports[0].split("/")[-1])
            else:
                with ZipFile('exports/export.zip', 'w') as zipped:
                    for elem2 in exports:
                        zipped.write(elem2, elem2.split("/")[-1])
                return send_file('exports/export.zip', 'export.zip')
    except ot.errors.UnoException as e:
        restart_soffice()
        if error_caught:
            return (
                error_format(e, "Internal server error on file opening. Please checks the README file, section "
                                "'Unsolvable problems' for more informations."),
                500
            )
        else:
            return fill_file(directory, file, json, True)


clean_temp_files()
