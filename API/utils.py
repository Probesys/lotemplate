"""
Copyright (C) 2023 Probesys
"""

from flask import Response, send_file

import lotemplate as ot

import glob
import os
import sys
from typing import Union

host='localhost'
port='200'
gworkers=0
scannedjson=''
maxtime=60
def start_soffice(workers,jsondir,maxt=60):
    global gworkers
    global my_lo
    global scannedjson
    global maxtime
    maxtime=maxt
    scannedjson=jsondir
    gworkers=workers
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    os.makedirs(scannedjson, exist_ok=True)
    clean_temp_files()
    my_lo=ot.start_multi_office(nb_env=workers)


def connexion():
   global my_lo
   cnx= ot.randomConnexion(my_lo)

   return cnx

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
    # I get more info on the exception
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    exception_message = str(exception)+' ; '+exc_type.__name__ + " in " + fname + " at line " + str(exc_tb.tb_lineno)

    formatted = (
        {
            'error': type(exception).__name__,
            'code': exception.code if isinstance(exception, ot.errors.LotemplateError) else type(exception).__name__,
            'message': message or exception_message,
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


    cnx = connexion()
    global scannedjson
    try:
        with ot.TemplateFromExt(f"uploads/{directory}/{name}", cnx, True,scannedjson) as temp:
            values = temp.variables
    except ot.errors.TemplateError as e:
        delete_file(directory, name)
        return error_format(e), 415
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
    cnx = connexion()
    global scannedjson
    with ot.TemplateFromExt(f"uploads/{directory}/{file}", cnx, True,scannedjson) as temp:
            variables = temp.variables
    return {'file': file, 'message': "Successfully scanned", 'variables': variables}


def fill_file(directory: str, file: str, json, error_caught=False) -> Union[tuple[dict, int], dict, tuple[str,Response]]:
    """
    fill the specified file

    :param directory: the directory where the file is
    :param file: the file to fill
    :param json: the json to fill the document with
    :param error_caught: specify if an error was already caught
    :return: a json and optionally an int which represent the status code to return
    """
    if  isinstance(json, list):
        json=json[0]
        print("####\nUsing a list of dict is DEPRECATED, you must directly send the dict.")
        print("See documentation.\n#######")
    cnx = connexion()
    global scannedjson
    try:
        with ot.TemplateFromExt(f"uploads/{directory}/{file}", cnx, True,scannedjson) as temp:

            length = len(json)
            is_name_present = type(json.get("name")) is str
            is_variables_present = type(json.get("variables")) is dict
            is_page_break_present = type(json.get("page_break")) is bool
            is_watermark_present = type(json.get("watermark")) is dict
            if (
                    not is_name_present
                    or not is_variables_present
            ):
                return 415, error_sim(
                    "JsonSyntaxError",
                    'api_invalid_instance_syntax',
                    "Each instance of the array in the json should be an object containing only 'name' - "
                    "a non-empty string, 'variables' - a non-empty object, optionally, 'page_break' - "
                    "a boolean and 'watermark' a json array.")

            try:
                json_variables = ot.convert_to_datas_template(json["variables"])
                temp.search_error(json_variables)
                temp.fill(json["variables"])
                if json.get('page_break', False):
                    temp.page_break()
                watermark=json.get("watermark",{})
                export_file=temp.export(json["name"],"exports",False,watermark)
                export_name=json["name"]
            except Exception as e:
                if 'export_name' in locals():
                    return ( export_file,error_format(e))
                else:
                    return ( "nofile",error_format(e))
            return (export_file,send_file(export_file, export_name))

    except Exception as e:
            return error_format(e), 500

