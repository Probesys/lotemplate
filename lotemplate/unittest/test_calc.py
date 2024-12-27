"""
Copyright (C) 2023 Probesys
"""

import unittest
import lotemplate as ot
from time import sleep
import subprocess
import filecmp
import os
import json

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


def compare_files_html(name: str ):

    base_path = 'lotemplate/unittest/files/content'

    def get_filename(ext: str):
        return base_path + '/' + name + '.' + ext

    temp = None
    if os.path.isfile(get_filename('ods')):
        temp = ot.TemplateFromExt(get_filename('ods'), cnx, True)

    if temp is None:
        if name == 'debug':
            return True
        else:
            raise FileNotFoundError('No file found for ' + name)

    temp.scan()
    temp.search_error(to_data(get_filename('json')))
    temp.fill(file_to_dict(get_filename('json')))

    if os.path.isfile(get_filename('unittest.html')):
        os.remove(get_filename('unittest.html'))
    temp.export(name+'.unittest.html',base_path, True)
    temp.close()
    with open(get_filename('unittest.html'), 'r+') as fp:
        # read an store all lines into list
        lines = fp.readlines()
        # move file pointer to the beginning of a file
        fp.seek(0)
        # truncate the file
        fp.truncate()

        # start writing lines
        # iterate line and line number
        for number, line in enumerate(lines):
            # delete line number 8,9,10
            # note: list index start from 0
            if number not in [ 7,8,9]:
                fp.write(line)


    response = filecmp.cmp(get_filename('unittest.html'),
                           get_filename('expected.html'))
    return response


class Test_calc(unittest.TestCase):

    def test_scan(self):
        self.assertEqual(
            {"TOTO": {"type": "text", "value": ""}, "second": {"type":
            "text", "value": ""}, "titi": {"type": "text", "value":
            ""}, "toto": {"type": "text", "value": ""}, "myvar":
            {"type": "text", "value": ""}, "foobar": {"type": "text",
            "value": ""}},
            (doc := ot.TemplateFromExt("lotemplate/unittest/files/templates/calc_variables.ods", cnx, False)).scan())
        doc.close()

    def test_var(self):
        self.assertTrue(compare_files_html('calc_variables'))


