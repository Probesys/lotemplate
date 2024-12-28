"""
Copyright (C) 2023 Probesys
"""


import lotemplate as ot
from time import sleep
import shlex,subprocess
import filecmp
import os
import json
from pypdf import PdfReader

def start_office():
   mylo=(ot.start_multi_office())
   sleep(2)
   cnx= ot.randomConnexion(mylo)
   return cnx


def file_to_dict(file_path: str) -> dict:
    if ot.is_network_based(file_path):
        return json.loads(urllib.request.urlopen(file_path).read())
    else:
        with open(file_path) as f:
            return json.loads(f.read())
def to_data(file: str):
    return ot.convert_to_datas_template(test_json_convertion.file_to_dict(file))


def to_data(file: str):
    return ot.convert_to_datas_template(file_to_dict(file))


def compare_files_html(name: str, cnx ):

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



def compare_files(name: str, format: str = 'txt',cnx = None):
    if format not in ['txt', 'pdf']:
        return False

    base_path = 'lotemplate/unittest/files/content'

    def get_filename(ext: str):
        return base_path + '/' + name + '.' + ext

    temp = None
    if os.path.isfile(get_filename('odt')):
        temp = ot.TemplateFromExt(get_filename('odt'), cnx, True)
    if os.path.isfile(get_filename('docx')):
        temp = ot.TemplateFromExt(get_filename('docx'), cnx, True)

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


