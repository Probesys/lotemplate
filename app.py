from flask import *
from werkzeug.utils import secure_filename

import ootemplate as ot
from ootemplate import err

import configparser
import glob
import os
from shutil import copyfile, rmtree
import subprocess
from copy import copy
from time import sleep
from typing import Union

app = Flask(__name__)
os.makedirs("uploads", exist_ok=True)
os.makedirs("exports", exist_ok=True)
for d in os.listdir("uploads"):
    for f in glob.glob(f"uploads/{d}/.~lock.*#"):
        os.remove(f)

config = configparser.ConfigParser()
config.read("config.ini")
host = config['Soffice']['host']
port = config['Soffice']['port']
subprocess.call(f'soffice "--accept=socket,host={host},port={port};urp;StarOffice.ServiceManager" &', shell=True)
sleep(1)
cnx = ot.Connexion(host, port)


def restart_soffice() -> None:
    """
    simply restart the soffice process

    :return: None
    """

    for d in os.listdir("uploads"):
        for f in glob.glob(f"uploads/{d}/.~lock.*#"):
            os.remove(f)

    subprocess.call(
        f'soffice "--accept=socket,host={cnx.host},port={cnx.port};urp;StarOffice.ServiceManager" &',
        shell=True
    )
    sleep(1)
    cnx.restart()


def delete_file(directory: str, name: str) -> None:
    """
    Deletes the given file and the temp files created by soffice
    :param directory: the directory containing the file to delete
    :param name: the file to delete
    :return: None
    """

    os.remove(f"uploads/{directory}/{name}")
    try:
        os.remove(f"uploads/{directory}/.~lock.{name}#")
    except:
        pass


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
                'variables': variables
            }
    )
    if message:
        formatted['message'] = message
    return formatted


def error_sim(exception: str, message: str, variables=dict({})) -> dict:
    """
    Simulate an error catch, ans return a error-formatted dict in the same way as error_format does

    :param exception: the exception name
    :param message: the message of the exception
    :param variables: the list of variables to join
    :return: the formatted dict
    """

    return {'error': exception, 'message': message, 'variables': variables}


def save_file(directory: str, f, name: str, error_catched=False) -> Union[tuple[dict, int], dict]:
    """
    upload a template file, and scan it.

    :param f: the file to save
    :param directory: the directory of the file
    :param name: the name of the file
    :param error_catched: specify if an error has been catched
    :return: a json, with the filename under which it was saved (key 'file'),
    and the scanned variables present in the template (key 'variables')
    """

    try:
        os.mkdir(f"uploads/{directory}")
    except:
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
    except err.TemplateInvalidFormat as e:
        delete_file(directory, name)
        return (
            error_format(e, "The given format is invalid. You can upload ODT, OTT, DOC, DOCX, HTML, RTF or TXT."),
            415
        )
    except err.UnoBridgeException as e:
        delete_file(directory, name)
        restart_soffice()
        if error_catched:
            return (
                error_format(e, "Internal server error on file opening. Please checks the README file, section "
                                "'Unsolvable problems' for more informations."),
                500
            )
        else:
            return save_file(directory, f, name, True)
    except err.UnoConnectionClosed as e:
        delete_file(directory, name)
        restart_soffice()
        if error_catched:
            return (
                error_format(e, "Internal server error : the soffice process keeps closing. Please check the error "
                                "for more help"),
                500
            )
        else:
            return save_file(directory, f, name, True)
    except err.TemplateException as e:
        delete_file(directory, name)
        return error_format(e), 415
    except Exception as e:
        delete_file(directory, name)
        return error_format(e), 500
    return {'file': name, 'message': "Successfully uploaded", 'variables': values}


def scan_file(directory: str, file: str, error_catched=False) -> Union[tuple[dict, int], dict]:
    """
    scans the specified file

    :param directory: the directory where the file is
    :param file: the file to scan
    :param error_catched: specify if an error was already catched
    :return: a json and optionaly an int which represent the status code to return
    """

    try:
        with ot.Template(f"uploads/{directory}/{file}", cnx, True) as temp:
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
            return scan_file(directory, file, True)
    return {'file': file, 'message': "Successfully scanned", 'variables': variables}


def fill_file(directory: str, file: str, format: str, json: dict, error_catched=False) -> Union[tuple[dict, int], dict]:
    """
    fill the specified file

    :param directory: the directory where the file is
    :param file: the file to fill
    :param format: the specified export format
    :param json: the json to fill the document with
    :param error_catched: specify if an error was already catched
    :return: a json and optionaly an int which represent the status code to return
    """

    try:
        json_variables = ot.convert_to_datas_template(file, json)
    except Exception as e:
        return error_format(e), 415
    try:
        with ot.Template(f"uploads/{directory}/{file}", cnx, True) as temp:
            try:
                temp.search_error(json_variables, "request_body")
                temp.fill(json)
                temp.export("exports/export." + format, True)
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
            return fill_file(directory, file, format, json, True)
    except err.UnoConnectionClosed as e:
        restart_soffice()
        if error_catched:
            return (
                error_format(e, "Internal server error : the soffice process keeps closing. Please check the error "
                                "for more help"),
                500
            )
        else:
            return fill_file(directory, file, format, json, True)


@app.route("/", methods=['PUT', 'GET'])
def main():
    if request.method == 'PUT':
        if 'directory' not in request.headers:
            return error_sim("BadRequest", "You must provide a valid format in the headers, key 'directory'",
                             {'key': 'directory'}), 400
        directory = request.headers['directory'].replace('/', '')
        if os.path.isdir(f"uploads/{directory}"):
            return error_sim("DirAlreadyExists", f"the specified directory {repr(directory)} already exists",
                             {'directory': directory}), 415
        os.mkdir(f"uploads/{directory}")
        return {'directory': directory, "message": "Successfully created"}
    elif request.method == 'GET':
        return jsonify(os.listdir("uploads"))


@app.route("/<directory>", methods=['PUT', 'DELETE', 'PATCH', 'GET'])
def directory(directory):
    if request.method == 'GET':
        if not os.path.isdir(f"uploads/{directory}"):
            return error_sim("DirNotFoundError", f"the specified directory {repr(directory)} doesn't exist",
                             {'directory': directory}), 415
        datas = []
        for file in os.listdir(f"uploads/{directory}"):
            file_info = scan_file(directory, file)
            if isinstance(file_info, tuple):
                return file_info
            file_info.pop('message')
            datas.append(file_info)
        return jsonify(datas)
    elif request.method == 'PUT':
        f = request.files.get('file')
        if not f:
            return error_sim("MissingFileError", "You must provide a valid file in the body, key 'file'",
                             {'key': 'file'}), 400
        return save_file(directory, f, secure_filename(f.filename))
    elif request.method == 'DELETE':
        if not os.path.isdir(f"uploads/{directory}"):
            return error_sim("DirNotFoundError", f"the specified directory {repr(directory)} doesn't exist",
                             {'directory': directory}), 415
        rmtree(f"uploads/{directory}")
        return {'directory': directory, 'message': 'The directory and all his content has been deleted'}
    elif request.method == 'PATCH':
        if not os.path.isdir(f"uploads/{directory}"):
            return error_sim("DirNotFoundError", f"the specified directory {repr(directory)} doesn't exist",
                             {'directory': directory}), 415
        if 'name' not in request.headers:
            return error_sim("BadRequest", "You must provide a valid name in the headers, key 'name'",
                             {'key': 'name'}), 400
        new_name = request.headers['name'].replace('/', '')
        if os.path.isdir(f"uploads/{new_name}"):
            return error_sim("DirAlreadyExists", f"the specified directory {repr(new_name)} already exists",
                             {'directory': new_name, 'original_directory': directory}), 415
        os.rename(f"uploads/{directory}", f"uploads/{new_name}")
        return {'directory': new_name,
                'old_directory': directory,
                "message": f"directory {directory} sucessfully renamed in {new_name}"}


@app.route("/<directory>/<file>", methods=['GET', 'PATCH', 'DELETE', 'POST'])
def file(directory, file):
    if not os.path.isdir(f"uploads/{directory}"):
        return error_sim("DirNotFoundError", f"the specified directory {repr(directory)} doesn't exist",
                         {'directory': directory}), 415
    if not os.path.isfile(f"uploads/{directory}/{file}"):
        return error_sim("FileNotFoundError", f"the specified file {repr(file)} doesn't exist in {repr(directory)}",
                         {'file': file, 'directory': directory}), 415
    if request.method == 'GET':
        return scan_file(directory, file)
    elif request.method == 'PATCH':
        copyfile(f"uploads/{directory}/{file}", f"uploads/temp_{file}")
        os.remove(f"uploads/{directory}/{file}")
        f = request.files.get('file')
        if not f:
            return error_sim("MissingFileError", "You must provide a valid file in the body, key 'file'",
                             {'key': 'file'}), 400
        datas = save_file(directory, f, file)
        if isinstance(datas, tuple):
            copyfile(f"uploads/temp_{file}", f"uploads/{directory}/{file}")
        os.remove(f"uploads/temp_{file}")
        return datas
    elif request.method == 'POST':
        if 'format' not in request.headers:
            return error_sim("BadRequest", "You must provide a valid format in the headers, key 'format'",
                             {'key': 'format'}), 400
        if not request.json:
            return error_sim("BadRequest", "You must provide a json in the body"), 400
        return fill_file(directory, file, request.headers['format'], request.json)
    elif request.method == 'DELETE':
        os.remove(f"uploads/{directory}/{file}")
        return {'directory': directory, 'file': file, 'message': "File successfully deleted"}


@app.route("/<directory>/<file>/download")
def download(directory, file):
    if not os.path.isdir(f"uploads/{directory}"):
        return error_sim("DirNotFoundError", f"the specified directory {repr(directory)} doesn't exist",
                         {'directory': directory}), 415
    if not os.path.isfile(f"uploads/{directory}/{file}"):
        return error_sim("FileNotFoundError", f"the specified file {repr(file)} doesn't exist in {repr(directory)}",
                         {'file': file, 'directory': directory}), 415
    return send_file(f"uploads/{directory}/{file}")
