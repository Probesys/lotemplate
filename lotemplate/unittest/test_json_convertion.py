"""
Copyright (C) 2023 Probesys
"""

import unittest
import lotemplate as ot
import json
from .test_function import file_to_dict


cnx = ot.start_multi_office()

class Generic(unittest.TestCase):

    def test_valid_empty(self):
        self.assertEqual({}, ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/empty.json")))

    def test_invalid_really_empty(self):
        with self.assertRaises(json.JSONDecodeError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/really_empty.json"))

    def test_invalid_syntax(self):
        with self.assertRaises(json.JSONDecodeError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/syntax_invalid.json"))

    def test_invalid_not_dict(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/not_dict.json"))

    def test_invalid_var_not_dict(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/invalid_var_not_dict.json"))

    def test_invalid_var_missing_type(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/invalid_var_missing_type.json"))

    def test_invalid_var_missing_value(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/invalid_var_missing_value.json"))

    def test_invalid_var_another_elem(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/invalid_var_another_elem.json"))

    def test_invalid_type_var_type(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/invalid_type_var_type.json"))

    def test_invalid_type_var(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/invalid_type_var.json"))


class Text(unittest.TestCase):

    def test_vars_valid(self):
        self.assertEqual(
            {
                "aerhh": {"type": "text", "value": ""},
                "h": {"type": "text", "value": ""},
                "rh": {"type": "text", "value": ""},
                "gjerg": {"type": "text", "value": ""},
                "aet": {"type": "text", "value": ""},
                "jean": {"type": "text", "value": ""}
            },
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/text_vars_valid.json"))
        )

    def test_invalid_null(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/text_vars_invalid_null.json"))


class Images(unittest.TestCase):

    def test_valid(self):
        self.assertEqual(
            {"image": {"type": "image", "value": ""}},
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/img_vars_valid.json"))
        )

    def test_two_valid(self):
        self.assertEqual(
            {"image": {"type": "image", "value": ""}, "image2": {"type": "image", "value": ""}},
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/img_two_vars_valid.json"))
        )

    def test_web_valid(self):
        self.assertEqual(
            {"image": {"type": "image", "value": ""}},
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/img_vars_valid_from_web.json"))
        )

    def test_invalid_empty_value(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict(
                "lotemplate/unittest/files/jsons/img_vars_invalid_empty_value.json"))

    def test_invalid_null_path(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict(
                "lotemplate/unittest/files/jsons/img_vars_invalid_null_path_type.json"))

    def test_invalid_path_type(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict(
                "lotemplate/unittest/files/jsons/img_vars_invalid_path_type.json"))

    def test_invalid_path(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/img_vars_invalid_path.json"))

    def test_invalid_path_from_web(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(file_to_dict(
                "lotemplate/unittest/files/jsons/img_vars_invalid_path_from_web.json"))


class Tables(unittest.TestCase):

    def test_valid(self):
        self.assertEqual(
            {
                "var": {"type": "table", "value": []},
                "var1": {"type": "table", "value": []},
                "var2": {"type": "table", "value": []}
            },
            ot.convert_to_datas_template(file_to_dict("lotemplate/unittest/files/jsons/tab_valid.json"))
        )

    def test_invalid_empty(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(
                file_to_dict("lotemplate/unittest/files/jsons/tab_invalid_empty.json")
            )

    def test_invalid_row_value(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(
                file_to_dict("lotemplate/unittest/files/jsons/tab_invalid_value_type_row.json")
            )

    def test_invalid_cell_value(self):
        with self.assertRaises(ot.errors.JsonSyntaxError):
            ot.convert_to_datas_template(
                file_to_dict("lotemplate/unittest/files/jsons/tab_invalid_value_type_cell.json")
            )


if __name__ == '__main__':
    unittest.main()
