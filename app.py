from flask import *

import ootemplate as ot
from ootemplate import err
import configparser
from werkzeug.utils import secure_filename
import os
from shutil import copyfile
import subprocess
from copy import copy
from time import sleep

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")
host = config['Connect']['host']
port = config['Connect']['port']
subprocess.call(f'soffice "--accept=socket,host={host},port={port};urp;StarOffice.ServiceManager" &', shell=True)
sleep(0.2)
cnx = ot.Connexion(host, port)


def restart_soffice():
    global cnx
    subprocess.call(f'soffice "--accept=socket,host={cnx.host},port={cnx.port};urp;StarOffice.ServiceManager" &',
                    shell=True)
    sleep(0.2)
    cnx = ot.Connexion(cnx.host, cnx.port)


def error_format(exception: Exception, message: str = None) -> dict:
    """
    put all informations about an error in a dictionary for better error handling when using the API.
    You can also overwrite the provided error message

    :param exception: the exception to format
    :param message: the message with which it should replace the provided error message
    :return: the formatted dictionary
    """

    class ReservedVariable(Exception):
        pass

    variables = copy(exception.__dict__)
    if 'file' in variables.keys():
        variables['file'] = variables['file'].split("/")[-1]
    if 'variables' in variables.keys():
        raise ReservedVariable(
            "The variable 'variables' is reserved for formatting, and so the exception cannot be formatted"
        )
    if 'error' in variables.keys():
        raise ReservedVariable(
            "The variable 'error' is reserved for formatting, and so the exception cannot be formatted"
        )
    if 'message' in variables.keys():
        raise ReservedVariable(
            "The variable 'message' is reserved for formatting, and so the exception cannot be formatted"
        )
    formatted = (
            {
                'error': type(exception).__name__,
                'message': str(exception),
                'variables': [elem for elem in variables.keys()]
            }
            | variables
    )
    if message:
        formatted['message'] = message
    return formatted


def error_sim(exception: str, message: str) -> dict:
    """
    Simulate an error catch, ans return a error-formatted dict in the same way as error_format does

    :param exception: the exception name
    :param message: the message of the exception
    :return: the formatted dict
    """

    return {'error': exception, 'message': message, 'variables': []}


def save_file(f, name: str, error_catched=False):
    """
    upload a template file, and scan it.

    :return: a json, with the filename under which it was saved (key 'file'),
    and the scanned variables present in the template (key 'variables')
    """

    if not f:
        return error_sim("MissingFileError", "You must provide a valid file in the body, key 'file'"), 400
    file_type = name.split(".")[-1]
    name_without_num = name
    if not os.path.isdir("uploads"):
        os.mkdir("uploads")
    i = 1
    while os.path.isfile(f"uploads/{name}"):
        name = name_without_num[:-(len(file_type) + 1)] + f"_{i}." + file_type
        i += 1
    f.stream.seek(0)
    f.save(f"uploads/{name}")
    try:
        with ot.Template(f"uploads/{name}", cnx, True) as temp:
            values = temp.variables
    except err.TemplateInvalidFormat as e:
        os.remove(f"uploads/{name}")
        return (
            error_format(e, "The given format is invalid. You can upload ODT, OTT, DOC, DOCX, HTML, RTF or TXT."),
            415
        )
    except err.UnoBridgeException as e:
        os.remove(f"uploads/{name}")
        restart_soffice()
        if error_catched:
            return (
                error_format(e, "Internal server error on file opening. Please checks the README file, section "
                                "'Unsolvable problems' for more informations."),
                500
            )
        else:
            return save_file(f, name, True)
    except err.UnoConnectionClosed as e:
        os.remove(f"uploads/{name}")
        restart_soffice()
        if error_catched:
            return (
                error_format(e, "Internal server error : the soffice process keeps closing. Please check the error "
                                "for more help"),
                500
            )
        else:
            return save_file(f, name, True)
    except err.TemplateVariableNotInLastRow as e:
        os.remove(f"uploads/{name}")
        return error_format(e), 415
    except Exception as e:
        os.remove(f"uploads/{name}")
        return error_format(e), 500
    return {'file': name, 'message': "Successfully uploaded", 'variables': values}


def scan_file(file: str, error_catched=False):
    print("test")
    try:
        with ot.Template(f"uploads/{file}", cnx, True) as temp:
            variables = temp.variables
    except err.UnoBridgeException as e:
        restart_soffice()
        if error_catched:
            return (
                error_format(e, "Internal server error on file opening. Please checks the README file, section "
                                "'Unsolvable problems' for more informations."),
                500
            )
        else:
            return scan_file(file, True)
    return {'file': file, 'message': "Successfully scanned", 'variables': variables}


def fill_file(file, format, json, error_catched=False):
    if not os.path.isdir("exports"):
        os.mkdir("exports")
    try:
        json_variables = ot.convert_to_datas_template(file, json)
    except Exception as e:
        return error_format(e), 415
    try:
        with ot.Template(f"uploads/{file}", cnx, True) as temp:
            try:
                temp.search_error(json_variables, "request_body")
                temp.fill(json)
                temp.export("exports/export." + format)
                return send_file("exports/export." + format,
                                 attachment_filename='export.' + format)
            except Exception as e:
                return error_format(e), 415
    except err.UnoBridgeException as e:
        restart_soffice()
        if error_catched:
            return (
                error_format(e, "Internal server error on file opening. Please checks the README file, section "
                                "'Unsolvable problems' for more informations."),
                500
            )
        else:
            return fill_file(file, format, json, True)
    except err.UnoConnectionClosed as e:
        restart_soffice()
        if error_catched:
            return (
                error_format(e, "Internal server error : the soffice process keeps closing. Please check the error "
                                "for more help"),
                500
            )
        else:
            return fill_file(file, format, json, True)


@app.route("/", methods=['POST'])
def main():
    f = request.files.get('file')
    if not f:
        return error_sim("MissingFileError", "You must provide a valid file in the body, key 'file'"), 400
    return save_file(f, secure_filename(f.filename))


@app.route("/<file>", methods=['GET', 'PUT', 'DELETE', 'POST'])
def document(file):
    if not os.path.isfile(f"uploads/{file}"):
        return error_sim("FileNotFound", "The specified file doesn't exist")
    if request.method == 'GET':
        return scan_file(file)
    elif request.method == 'PUT':
        copyfile(f"uploads/{file}", f"uploads/temp_{file}")
        os.remove(f"uploads/{file}")
        f = request.files.get('file')
        datas = save_file(f, file)
        if isinstance(datas, tuple):
            copyfile(f"uploads/temp_{file}", f"uploads/{file}")
        os.remove(f"uploads/temp_{file}")
        return datas
    elif request.method == 'POST':
        if 'format' not in request.headers:
            return error_sim("BadRequest", "You must provide a valid format in the headers, key 'format'"), 400
        if not request.json:
            return error_sim("BadRequest", "You must provide a json in the body"), 400
        return fill_file(file, request.headers['format'], request.json)
    elif request.method == 'DELETE':
        os.remove(f"uploads/{file}")
        return {'file': file, 'message': "File successfully deleted"}
