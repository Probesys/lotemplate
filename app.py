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


@app.route("/", methods=['POST'])
def main():
    """
    upload a template file, and scan it.

    :return: a json, with the filename under which it was saved (key 'file'),
    and the scanned variables present in the template (key 'variables')
    """
    f = request.files.get('file')
    if not f:
        return error_sim("MissingFileError", "You must provide a valid file in the body, key 'file'"), 400
    name = secure_filename(f.filename)
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
    return {'file': name, 'variables': values}


@app.route("/<file>", methods=['GET', 'PUT', 'DELETE', 'POST'])
def document(file):
    if request.method == 'GET':
        pass  # TODO: re-scan the template
    elif request.method == 'PUT':
        pass  # TODO: edit the template
    elif request.method == 'POST':
        pass  # TODO: send json and return the filled template
    elif request.method == 'DELETE':
        pass  # TODO: remove the template file
