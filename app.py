"""
Copyright (C) 2023 Probesys
"""

from flask import *
from werkzeug.utils import secure_filename

import os
from shutil import copyfile, rmtree

from API import utils

app = Flask(__name__)


@app.route("/", methods=['PUT', 'GET'])
def main_route():
    if request.headers.get('secret_key', '') != os.environ.get('SECRET_KEY', ''):
        return utils.error_sim(
            'ApiError', 'invalid_secret_key', f"The secret key is invalid or not given", {'key': 'secret_key'}), 401
    if request.method == 'PUT':
        if 'directory' not in request.headers:
            return utils.error_sim(
                'ApiError', 'missing_header_key', "You must provide a valid name in the headers, key 'directory'",
                {'key': 'directory'}), 400
        directory = request.headers['directory'].replace('/', '')
        if os.path.isdir(f"uploads/{directory}"):
            return utils.error_sim(
                'ApiError', 'dir_already_exists', f"the specified directory {repr(directory)} already exists",
                {'directory': directory}), 415
        os.mkdir(f"uploads/{directory}")
        return {'directory': directory, "message": "Successfully created"}
    elif request.method == 'GET':
        return jsonify(os.listdir("uploads"))


@app.route("/<directory>", methods=['PUT', 'DELETE', 'PATCH', 'GET'])
def directory_route(directory):
    if request.headers.get('secret_key', '') != os.environ.get('SECRET_KEY', ''):
        return utils.error_sim(
            'ApiError', 'invalid_secret_key', f"The secret key is invalid or not given", {'key': 'secret_key'}), 401
    if not os.path.isdir(f"uploads/{directory}") and request.method != 'PUT':
        return utils.error_sim(
            'ApiError', 'dir_not_found', f"the specified directory {repr(directory)} doesn't exist",
            {'directory': directory}), 415
    if request.method == 'GET':
        datas = []
        for file in os.listdir(f"uploads/{directory}"):
            file_info = utils.scan_file(directory, file)
            if isinstance(file_info, tuple):
                return file_info
            file_info.pop('message')
            datas.append(file_info)
        return jsonify(datas)
    elif request.method == 'PUT':
        f = request.files.get('file')
        if not f:
            return utils.error_sim(
                'ApiError', 'missing_body_key', "You must provide a valid file in the body, key 'file'",
                {'key': 'file'}), 400
        return utils.save_file(directory, f, secure_filename(f.filename))
    elif request.method == 'DELETE':
        rmtree(f"uploads/{directory}")
        return {'directory': directory, 'message': 'The directory and all his content has been deleted'}
    elif request.method == 'PATCH':
        if 'name' not in request.headers:
            return utils.error_sim(
                'ApiError', 'missing_header_key', "You must provide a valid name in the headers, key 'name'",
                {'key': 'name'}), 400
        new_name = request.headers['name'].replace('/', '')
        if os.path.isdir(f"uploads/{new_name}"):
            return utils.error_sim(
                'ApiError', 'dir_already_exists', f"the specified directory {repr(new_name)} already exists",
                {'directory': new_name, 'original_directory': directory}), 415
        os.rename(f"uploads/{directory}", f"uploads/{new_name}")
        return {'directory': new_name,
                'old_directory': directory,
                "message": f"directory {directory} successfully renamed in {new_name}"}


@app.route("/<directory>/<file>", methods=['GET', 'PATCH', 'DELETE', 'POST'])
def file_route(directory, file):
    if request.headers.get('secret_key', '') != os.environ.get('SECRET_KEY', ''):
        return utils.error_sim(
            'ApiError', 'invalid_secret_key', f"The secret key is invalid or not given", {'key': 'secret_key'}), 401
    if not os.path.isdir(f"uploads/{directory}"):
        return utils.error_sim(
            'ApiError', 'dir_not_found', f"the specified directory {repr(directory)} doesn't exist",
            {'directory': directory}), 415
    if not os.path.isfile(f"uploads/{directory}/{file}"):
        return utils.error_sim(
            'ApiError', 'file_not_found', f"the specified file {repr(file)} doesn't exist in {repr(directory)}",
            {'file': file, 'directory': directory}), 415
    if request.method == 'GET':
        return utils.scan_file(directory, file)
    elif request.method == 'PATCH':
        copyfile(f"uploads/{directory}/{file}", f"uploads/temp_{file}")
        os.remove(f"uploads/{directory}/{file}")
        f = request.files.get('file')
        if not f:
            return utils.error_sim(
                'ApiError', 'missing_body_key', "You must provide a valid file in the body, key 'file'",
                {'key': 'file'}), 400
        datas = utils.save_file(directory, f, file)
        if isinstance(datas, tuple):
            copyfile(f"uploads/temp_{file}", f"uploads/{directory}/{file}")
        os.remove(f"uploads/temp_{file}")
        return datas
    elif request.method == 'POST':
        if not request.json:
            return utils.error_sim('ApiError', 'missing_json', "You must provide a json in the body"), 400
        return utils.fill_file(directory, file, request.json)
    elif request.method == 'DELETE':
        os.remove(f"uploads/{directory}/{file}")
        return {'directory': directory, 'file': file, 'message': "File successfully deleted"}


@app.route("/<directory>/<file>/download")
def download_route(directory, file):
    if request.headers.get('secret_key', '') != os.environ.get('SECRET_KEY', ''):
        return utils.error_sim(
            'ApiError', 'invalid_secret_key', f"The secret key is invalid or not given", {'key': 'secret_key'}), 401
    if not os.path.isdir(f"uploads/{directory}"):
        return utils.error_sim(
            'ApiError', 'dir_not_found', f"the specified directory {repr(directory)} doesn't exist",
            {'directory': directory}), 415
    if not os.path.isfile(f"uploads/{directory}/{file}"):
        return utils.error_sim(
            'ApiError', 'file_not_found', f"the specified file {repr(file)} doesn't exist in {repr(directory)}",
            {'file': file, 'directory': directory}), 415
    return send_file(f"uploads/{directory}/{file}")
