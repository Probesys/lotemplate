import json
import unittest
import urllib.request
import ootemplate as ot


def file_to_dict(file_path: str) -> dict:
    if ot.is_network_based(file_path):
        return json.loads(urllib.request.urlopen(file_path).read())
    else:
        with open(file_path) as f:
            return json.loads(f.read())


class Generic(unittest.TestCase):

    def test_instance_empty(self):
        with self.assertRaises(ot.err.JsonEmptyInstance):
            ot.convert_to_datas_template("instance_empty.json", file_to_dict("files/jsons/instance_empty.json"))

    def test_invalid_empty(self):
        with self.assertRaises(ot.err.JsonEmptyBase):
            ot.convert_to_datas_template("empty.json", file_to_dict("files/jsons/empty.json"))

    def test_invalid_really_empty(self):
        with self.assertRaises(json.JSONDecodeError):
            ot.convert_to_datas_template("really_empty.json", file_to_dict("files/jsons/really_empty.json"))

    def test_invalid_syntax(self):
        with self.assertRaises(json.JSONDecodeError):
            ot.convert_to_datas_template("syntax_invalid.json", file_to_dict("files/jsons/syntax_invalid.json"))

    def test_invalid_not_list(self):
        with self.assertRaises(ot.err.JsonInvalidBaseValueType):
            ot.convert_to_datas_template("not_list.json", file_to_dict("files/jsons/not_list.json"))

    def test_invalid_instance_not_dict(self):
        with self.assertRaises(ot.err.JsonInvalidInstanceValueType):
            ot.convert_to_datas_template("instance_not_dict.json", file_to_dict("files/jsons/instance_not_dict.json"))

    def test_invalid_null(self):
        with self.assertRaises(ot.err.JsonInvalidValueType):
            ot.convert_to_datas_template(
                "text_vars_invalid_null.json",
                file_to_dict("files/jsons/text_vars_invalid_null.json")
            )

    def test_multiple_instances(self):
        self.assertEqual(
            [
                {"aerhh": "", "h": "", "rh": "", "gjerg": "", "aet": "", "jean": ""},
                {"aerhh": "", "h": "", "rh": "", "gjerg": "", "aet": "", "jean": ""}
            ],
            ot.convert_to_datas_template("multiple_instances.json", file_to_dict("files/jsons/multiple_instances.json"))
        )

    def test_invalid_multiple_instances(self):
        with self.assertRaises(ot.err.JsonInvalidValueType):
            ot.convert_to_datas_template(
                "invalid_multiple_instances.json",
                file_to_dict("files/jsons/invalid_multiple_instances.json")
            )


class Text(unittest.TestCase):

    def test_vars_valid(self):
        self.assertEqual(
            [{"aerhh": "", "h": "", "rh": "", "gjerg": "", "aet": "", "jean": ""}],
            ot.convert_to_datas_template("text_vars_valid.json", file_to_dict("files/jsons/text_vars_valid.json"))
        )


class Images(unittest.TestCase):

    def test_valid(self):
        self.assertEqual(
            [{"image": [""]}], ot.convert_to_datas_template(
                "img_vars_valid",
                file_to_dict("files/jsons/img_vars_valid.json")
            )
        )

    def test_two_valid(self):
        self.assertEqual(
            [{"image": [""], "image2": [""]}],
            ot.convert_to_datas_template("img_two_vars_valid", file_to_dict("files/jsons/img_two_vars_valid.json"))
        )

    def test_web_valid(self):
        self.assertEqual(
            [{"image": [""]}],
            ot.convert_to_datas_template(
                "img_vars_valid_from_web",
                file_to_dict("files/jsons/img_vars_valid_from_web.json")
            )
        )

    def test_invalid_empty_value(self):
        with self.assertRaises(ot.err.JsonImageEmpty):
            ot.convert_to_datas_template(
                "img_vars_invalid_empty_value.json", file_to_dict("files/jsons/img_vars_invalid_empty_value.json")
            )

    def test_invalid_null_path(self):
        with self.assertRaises(ot.err.JsonImageInvalidArgumentType):
            ot.convert_to_datas_template(
                "img_vars_invalid_null_path_type", file_to_dict("files/jsons/img_vars_invalid_null_path_type.json")
            )

    def test_invalid_other_argument(self):
        with self.assertRaises(ot.err.JsonImageInvalidArgument):
            ot.convert_to_datas_template(
                "img_vars_invalid_other_argument", file_to_dict("files/jsons/img_vars_invalid_other_argument.json")
            )

    def test_invalid_path_type(self):
        with self.assertRaises(ot.err.JsonImageInvalidArgumentType):
            ot.convert_to_datas_template(
                "img_vars_invalid_path_type", file_to_dict("files/jsons/img_vars_invalid_path_type.json")
            )

    def test_invalid_path(self):
        with self.assertRaises(ot.err.JsonImageInvalidPath):
            ot.convert_to_datas_template(
                "img_vars_invalid_path", file_to_dict("files/jsons/img_vars_invalid_path.json")
            )

    def test_invalid_path_from_web(self):
        with self.assertRaises(ot.err.JsonImageInvalidPath):
            ot.convert_to_datas_template(
                "img_vars_invalid_path_from_web", file_to_dict("files/jsons/img_vars_invalid_path_from_web.json")
            )


class Tables(unittest.TestCase):

    def test_valid(self):
        self.assertEqual(
            [{"tab": {"var": [""]}, "tab2": {"var1": [""], "var2": [""]}}],
            ot.convert_to_datas_template("tab_valid", file_to_dict("files/jsons/tab_valid.json"))
        )

    def test_invalid_empty_table(self):
        with self.assertRaises(ot.err.JsonEmptyTable):
            ot.convert_to_datas_template(
                "tab_invalid_empty_table", file_to_dict("files/jsons/tab_invalid_empty_table.json")
            )

    def test_invalid_empty_row(self):
        with self.assertRaises(ot.err.JsonEmptyTableVariable):
            ot.convert_to_datas_template(
                "tab_invalid_empty_row", file_to_dict("files/jsons/tab_invalid_empty_row.json")
            )

    def test_invalid_row_value(self):
        with self.assertRaises(ot.err.JsonInvalidTableValueType):
            ot.convert_to_datas_template(
                "tab_invalid_value_type_row", file_to_dict("files/jsons/tab_invalid_value_type_row.json")
            )

    def test_invalid_cell_value(self):
        with self.assertRaises(ot.err.JsonInvalidRowValueType):
            ot.convert_to_datas_template(
                "tab_invalid_value_type_cell", file_to_dict("files/jsons/tab_invalid_value_type_cell.json")
            )


if __name__ == '__main__':
    unittest.main()