"""
Copyright (C) 2023 Probesys
"""

import unittest
import lotemplate as ot

from test_function import compare_files 


cnx=ot.start_multi_office()

class Text(unittest.TestCase):

    def test_html(self):
        self.assertTrue(compare_files('html',cnx=cnx))

    def test_html_missing_endhtml(self):
        with self.assertRaises(ot.errors.TemplateError):
            self.assertTrue(compare_files('html_missing_endhtml',cnx=cnx))

    def test_for(self):
        self.assertTrue(compare_files('for',cnx=cnx))

    def test_for_inside_if(self):
        self.assertTrue(compare_files('for_inside_if',cnx=cnx))

    def test_vars(self):
        self.assertTrue(compare_files('text_vars',cnx=cnx))

    def test_if(self):
        self.assertTrue(compare_files('if',cnx=cnx))

    def test_if_empty(self):
        self.assertTrue(compare_files('if_empty',cnx=cnx))

    def test_if_contains(self):
        self.assertTrue(compare_files('if_contains',cnx=cnx))

    def test_function_variable(self):
        self.assertTrue(compare_files('function_variable',cnx=cnx))

    def test_if_recursive(self):
        self.assertTrue(compare_files('if_recursive',cnx=cnx))

    def test_if_inside_for(self):
        self.assertTrue(compare_files('if_inside_for',cnx=cnx))

    def test_html_vars(self):
        self.assertTrue(compare_files('html_vars',cnx=cnx))

    def test_table(self):
        self.assertTrue(compare_files('table',cnx=cnx))

    def test_image(self):
        self.assertTrue(compare_files('image',cnx=cnx))

    def test_counter(self):
        self.assertTrue(compare_files('counter',cnx=cnx))

    def test_text_var_in_header(self):
        self.assertTrue(compare_files('text_var_in_header', 'pdf',cnx=cnx))

    def test_too_many_endif_strange(self):
        self.assertTrue(compare_files('too_many_endif_strange',cnx=cnx))

    def test_debug(self):
        self.assertTrue(compare_files('debug',cnx=cnx))
