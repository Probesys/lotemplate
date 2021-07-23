from flask import *
import ootemplate as ot

app = Flask(__name__)


@app.route("/", methods=['POST'])
def main():
    pass  # TODO: send and scan a template


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
