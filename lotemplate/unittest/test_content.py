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
from pypdf import PdfReader

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


def compare_files(name: str, format: str = 'txt'):
    if format not in ['txt', 'pdf']:
        return False

    base_path = 'lotemplate/unittest/files/content'

    def get_filename(ext: str):
        return base_path + '/' + name + '.' + ext

    temp = None
    if os.path.isfile(get_filename('odt')):
        temp = ot.WriterTemplate(get_filename('odt'), cnx, True)
    if os.path.isfile(get_filename('docx')):
        temp = ot.WriterTemplate(get_filename('docx'), cnx, True)

    if temp is None:
        if name == 'debug':
            return True
        else:
            raise FileNotFoundError('No file found for ' + name)

    temp.scan()
    temp.search_error(to_data(get_filename('json')))
    temp.fill(file_to_dict(get_filename('json')))

    if os.path.isfile(get_filename('unittest.'+format)):
        os.remove(get_filename('unittest.'+format))
    temp.export(name+'.unittest.'+format,base_path, True)
    # temp.close()
    if os.path.isfile(get_filename('unittest.odt')):
        os.remove(get_filename('unittest.odt'))
    temp.export(name+'.unittest.odt',base_path, True)
    temp.close()

    # The PDF format is used to test some documents with headers or footers that are not supported by the text saveAs from
    # LibreOffice. The PDF is then converted to text to compare with the expected text.
    if format == 'pdf':
        # convert to text
        reader = PdfReader(get_filename('unittest.pdf'))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        if os.path.isfile(get_filename('unittest.txt')):
            os.remove(get_filename('unittest.txt'))
        with open(get_filename('unittest.txt'), 'w') as f:
            f.write(text)

    response = filecmp.cmp(get_filename('unittest.txt'), get_filename('expected.txt'))
    return response


class Text(unittest.TestCase):

    def test_html(self):
        self.assertTrue(compare_files('html'))

    def test_html_missing_endhtml(self):
        with self.assertRaises(ot.errors.TemplateError):
            self.assertTrue(compare_files('html_missing_endhtml'))

    def test_for(self):
        self.assertTrue(compare_files('for'))

    def test_for_inside_if(self):
        self.assertTrue(compare_files('for_inside_if'))

    def test_vars(self):
        self.assertTrue(compare_files('text_vars'))

    def test_if(self):
        self.assertTrue(compare_files('if'))

    def test_if_empty(self):
        self.assertTrue(compare_files('if_empty'))

    def test_if_contains(self):
        self.assertTrue(compare_files('if_contains'))

    def test_function_variable(self):
        self.assertTrue(compare_files('function_variable'))

    def test_if_recursive(self):
        self.assertTrue(compare_files('if_recursive'))

    def test_if_inside_for(self):
        self.assertTrue(compare_files('if_inside_for'))

    def test_html_vars(self):
        self.assertTrue(compare_files('html_vars'))

    def test_table(self):
        self.assertTrue(compare_files('table'))

    def test_image(self):
        self.assertTrue(compare_files('image'))

    def test_counter(self):
        self.assertTrue(compare_files('counter'))

    def test_text_var_in_header(self):
        self.assertTrue(compare_files('text_var_in_header', 'pdf'))

    def test_too_many_endif_strange(self):
        self.assertTrue(compare_files('too_many_endif_strange'))

    def test_debug(self):
        self.assertTrue(compare_files('debug'))
