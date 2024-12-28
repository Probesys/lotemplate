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
from test_function import *


cnx = start_office()


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
        self.assertTrue(compare_files_html('calc_variables',cnx))


