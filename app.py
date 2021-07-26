from copy import copy

from flask import *
import ootemplate as ot
from ootemplate import err
import configparser
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")
cnx = ot.Connexion(config['Connect']['host'], config['Connect']['port'])


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


def save_file(f, name):
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
        return (
            error_format(e, "Internal server error on file opening. Please checks the README file, section "
                            "'Unsolvable problems' for more informations."),
            500
        )
    except err.TemplateVariableNotInLastRow as e:
        os.remove(f"uploads/{name}")
        return (
            error_format(e, f"The variable {repr(e.variable)} (table {repr(e.table)}) isn't in the last row (got: row "
                            f"{repr(e.row)}, expected: row {repr(e.expected_row)})"),
            415
        )
    return {'file': name, 'message': "Successfully uploaded", 'variables': values}


@app.route("/", methods=['POST'])
def main():
    f = request.files.get('file')
    return save_file(f, secure_filename(f.filename))


@app.route("/<file>", methods=['GET', 'PUT', 'DELETE', 'POST'])
def document(file):
    if not os.path.isfile(f"uploads/{file}"):
        return error_sim("FileNotFound", "The specified file doesn't exist")
    if request.method == 'GET':
        try:
            with ot.Template(f"uploads/{file}", cnx, True) as temp:
                variables = temp.variables
        except err.UnoBridgeException as e:
            return (
                error_format(e, "Internal server error on file opening. Please checks the README file, section "
                                "'Unsolvable problems' for more informations."),
                500
            )
        return {'file': file, 'message': "Successfully scanned", 'variables': variables}
    elif request.method == 'PUT':
        os.remove(f"uploads/{file}")
        f = request.files.get('file')
        return save_file(f, file)
    elif request.method == 'POST':
        if 'format' not in request.headers:
            return error_sim("MissingFileError", "You must provide a valid format in the headers, key 'format'"), 400
        if not os.path.isdir("exports"):
            os.mkdir("exports")
        try:
            json_variables = ot.convert_to_datas_template(file, request.json)
        except Exception as e:
            return error_format(e), 400
        try:
            with ot.Template(f"uploads/{file}", cnx, True) as temp:
                try:
                    temp.search_error(json_variables, file)
                    temp.fill(request.json)
                    temp.export("exports/export." + request.headers['format'])
                    return send_file("exports/export." + request.headers['format'],
                                     attachment_filename='export.' + request.headers['format'])
                except Exception as e:
                    return error_format(e), 400
        except err.UnoBridgeException as e:
            return (
                error_format(e, "Internal server error on file opening. Please checks the README file, section "
                                "'Unsolvable problems' for more informations."),
                500
            )
    elif request.method == 'DELETE':
        os.remove(f"uploads/{file}")
        return {'file': file, 'message': "File successfully deleted"}, 200
