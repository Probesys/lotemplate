import json
import unittest
import urllib.request

import main as ootemplate

connexion = ootemplate.Connexion("localhost", "2002")


def file_to_dict(file_path: str):
    if ootemplate.is_network_based(file_path):
        return json.loads(urllib.request.urlopen(file_path).read())
    else:
        with open(file_path) as f:
            return json.loads(f.read())


class Text(unittest.TestCase):

    def test_vars_valid(self):
        self.assertEqual({"aerhh": "", "h": "", "rh": "", "gjerg": "", "aet": "", "jean": ""},
                         ootemplate.convert_to_datas_template(
                             "text_vars_valid.json", file_to_dict("files/jsons/text_vars_valid.json")))

    def test_empty(self):
        self.assertEqual({},
                         ootemplate.convert_to_datas_template(
                             "empty.json", file_to_dict("files/jsons/empty.json")))

    def test_really_empty(self):
        with self.assertRaises(json.JSONDecodeError):
            ootemplate.convert_to_datas_template("really_empty.json", file_to_dict("files/jsons/really_empty.json"))

    def test_invalid_syntax(self):
        with self.assertRaises(json.JSONDecodeError):
            ootemplate.convert_to_datas_template("syntax_invalid.json", file_to_dict("files/jsons/syntax_invalid.json"))

    def test_not_dict(self):
        with self.assertRaises(ootemplate.err.JsonIncorrectValueType):
            ootemplate.convert_to_datas_template("not_dict.json", file_to_dict("files/jsons/not_dict.json"))

    def test_invalid_null(self):
        with self.assertRaises(ootemplate.err.JsonIncorrectValueType):
            ootemplate.convert_to_datas_template(
                "text_vars_invalid_null.json", file_to_dict("files/jsons/text_vars_invalid_null.json"))


if __name__ == '__main__':
    unittest.main()
