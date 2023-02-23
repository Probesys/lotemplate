"""
Copyright (C) 2023 Probesys
"""

import unittest
import json
import filecmp
import os
import urllib.request
import lotemplate as ot
from time import sleep
import subprocess

subprocess.call(f'soffice "--accept=socket,host=localhost,port=2002;urp;StarOffice.ServiceManager" &', shell=True)
sleep(2)
cnx = ot.Connexion("localhost", "2002")

def file_to_dict(file_path: str) -> dict:
    if ot.is_network_based(file_path):
        return json.loads(urllib.request.urlopen(file_path).read())
    else:
        with open(file_path) as f:
            return json.loads(f.read())

def to_data(file: str):
    return ot.convert_to_datas_template(file_to_dict(file))

def compareFiles(name: str):
    basePath = 'lotemplate/unittest/files/content'

    def getFilename(ext: str):
        return basePath+'/'+name+'.'+ext

    temp = ot.Template(getFilename('odt'), cnx, True)
    temp.search_error(to_data(getFilename('json')))
    temp.fill(file_to_dict(getFilename('json')))

    if os.path.isfile(getFilename('unittest.txt')):
        os.remove(getFilename('unittest.txt'))
    temp.export(getFilename('unittest.txt'), True)
    temp.close
    response = filecmp.cmp(getFilename('unittest.txt'), getFilename('expected.txt'))
    if os.path.isfile(getFilename('unittest.txt')):
        os.remove(getFilename('unittest.txt'))
    return response


class Text(unittest.TestCase):

    def test_vars(self):
        self.assertTrue(compareFiles('text_vars'))

    def test_if(self):
        self.assertTrue(compareFiles('if'))
