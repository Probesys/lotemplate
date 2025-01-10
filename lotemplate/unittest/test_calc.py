"""
Copyright (C) 2023 Probesys
"""
import unittest

import lotemplate as ot
from lotemplate.unittest.test_function import compare_files_html 

cnx = ot.start_multi_office()


class Test_calc(unittest.TestCase):

    def test_scan(self):
        self.assertEqual(
            {"TOTO": {"type": "text", "value": ""}, "second": {"type":
            "text", "value": ""}, "titi": {"type": "text", "value":
            ""}, "toto": {"type": "text", "value": ""}, "myvar":
            {"type": "text", "value": ""}, "foobar": {"type": "text",
            "value": ""}},
            (doc := ot.TemplateFromExt("lotemplate/unittest/files/templates/calc_variables.ods", ot.randomConnexion(cnx), False)).scan())
        doc.close()

    def test_var(self):
        self.assertTrue(compare_files_html('calc_variables',cnx))

    def test_table(self):
        self.assertTrue(compare_files_html('calc_table',cnx))



