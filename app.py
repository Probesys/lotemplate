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


@app.route("/", methods=['POST'])
def main():
    """
    upload a template file, and scan it.

    :return: a json, with the filename under which it was saved (key 'file'),
    and the scanned variables present in the template (key 'variables')
    """
    f = request.files.get('file')
    if not f:
        return "You must provide a valid file in the body, key 'file'", 400
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
    except err.TemplateInvalidFormat:
        os.remove(f"uploads/{name}")
        return "The given format is invalid. You can upload ODT, OTT, DOC, DOCX, HTML, RTF or TXT.", 415
    except err.UnoBridgeException:
        return "Internal server error on file opening. Please checks the README file, section 'Unsolvable problems' " \
               "for more informations.", 500
    except err.TemplateVariableNotInLastRow as e:
        return f"The variable {repr(e.variable)} (table {repr(e.table)}) isn't in the last row (got: row " \
               f"{repr(e.row)}, expected: row {repr(e.expected_row)})", 415
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
