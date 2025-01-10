"""
Copyright (C) 2023 Probesys
"""

import unittest
import lotemplate as ot
from lotemplate.unittest.test_function import to_data  

cnx=ot.start_multi_office()


class Text(unittest.TestCase):

    temp = ot.TemplateFromExt("lotemplate/unittest/files/comparaison/text_vars.odt", ot.randomConnexion(cnx), True)

    def test_valid(self):
        self.temp.search_error(to_data("lotemplate/unittest/files/comparaison/text_vars_valid.json"))

    def test_invalid_supplement_variable(self):
        """
        Check that there is no exception anymore where there is an unknown variable in the json
        """
        self.temp.search_error(to_data("lotemplate/unittest/files/comparaison/text_vars_invalid_variable.json"))

    def test_invalid_missing_variable(self):
        with self.assertRaises(ot.errors.JsonComparaisonError):
            self.temp.search_error(
                to_data("lotemplate/unittest/files/comparaison/text_vars_invalid_missing_variable.json"))

    def test_invalid_incorrect_value(self):
        with self.assertRaises(ot.errors.JsonComparaisonError):
            self.temp.search_error(to_data("lotemplate/unittest/files/comparaison/text_vars_incorrect_value.json"))

    temp.close()

    temp_tab = ot.TemplateFromExt("lotemplate/unittest/files/comparaison/static_tab.odt", ot.randomConnexion(cnx), True)

    def test_tab_valid(self):
        self.temp_tab.search_error(to_data("lotemplate/unittest/files/comparaison/static_tab_valid.json"))

    temp_tab.close()


class Tables(unittest.TestCase):

    temp = ot.TemplateFromExt("lotemplate/unittest/files/comparaison/two_row_tab_varied.odt", ot.randomConnexion(cnx), True)

    def test_valid(self):
        self.temp.search_error(to_data("lotemplate/unittest/files/comparaison/two_row_tab_varied_valid.json"))

    def test_invalid_missing_variable(self):
        with self.assertRaises(ot.errors.JsonComparaisonError):
            self.temp.search_error(to_data(
                "lotemplate/unittest/files/comparaison/two_row_tab_varied_invalid_missing_argument_all_rows.json"))

    def test_invalid_unknown_variable(self):
        """
        Check that there is no exception anymore where there is an unknown variable in the json
        """
        self.temp.search_error(to_data(
            "lotemplate/unittest/files/comparaison/two_row_tab_varied_invalid_unknown_argument.json"))

    temp.close()


class Images(unittest.TestCase):

    temp = ot.TemplateFromExt("lotemplate/unittest/files/comparaison/img_vars.odt", ot.randomConnexion(cnx), True)

    def test_valid(self):
        self.temp.search_error(to_data("lotemplate/unittest/files/comparaison/img_vars_valid.json"))

    def test_invalid_unknown_variable(self):
        """
        Check that there is no exception anymore where there is an unknown variable in the json
        """
        self.temp.search_error(to_data("lotemplate/unittest/files/comparaison/img_vars_invalid_other_image.json"))

    temp.close()


if __name__ == '__main__':
    unittest.main()
