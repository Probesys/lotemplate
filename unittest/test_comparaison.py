import unittest
import main as ootemplate
import test_json_convertion

cnx = ootemplate.Connexion("localhost", "2002")


def to_data_list(file: str) -> dict:
    return {file: ootemplate.convert_to_datas_template(file, test_json_convertion.file_to_dict(file))}


class Text(unittest.TestCase):

    temp = ootemplate.Template("unittest/files/comparaison/text_vars.odt", cnx, False)

    def test_valid(self):
        datas = to_data_list("files/comparaison/text_vars_valid.json")
        self.assertEqual(datas, self.temp.compare_variables(datas))

    def test_invalid_supplement_variable(self):
        with self.assertRaises(ootemplate.err.JsonUnknownVariable):
            self.temp.compare_variables(to_data_list("files/comparaison/text_vars_invalid_variable.json"))

    def test_invalid_missing_variable(self):
        with self.assertRaises(ootemplate.err.JsonMissingRequiredVariable):
            self.temp.compare_variables(to_data_list("files/comparaison/text_vars_invalid_missing_variable.json"))

    def test_invalid_incorrect_value(self):
        with self.assertRaises(ootemplate.err.JsonIncorrectValueType):
            self.temp.compare_variables(to_data_list("files/comparaison/text_vars_incorrect_value.json"))

    temp_tab = ootemplate.Template("unittest/files/comparaison/static_tab.odt", cnx, False)

    def test_tab_valid(self):
        datas = to_data_list("files/comparaison/static_tab_valid.json")
        self.assertEqual(datas, self.temp.compare_variables(datas))


class Tables(unittest.TestCase):

    temp = ootemplate.Template("unittest/files/comparaison/two_row_tab_varied.odt", cnx, False)

    def test_valid(self):
        datas = to_data_list("files/comparaison/two_row_tab_varied_valid.json")
        self.assertEqual(datas, self.temp.compare_variables(datas))

    def test_invalid_missing_variable(self):
        with self.assertRaises(ootemplate.err.JsonMissingRequiredVariable):
            self.temp.compare_variables(to_data_list(
                "files/comparaison/two_row_tab_varied_invalid_missing_argument_all_rows.json"
            ))

    def test_invalid_unknown_variable(self):
        with self.assertRaises(ootemplate.err.JsonUnknownVariable):
            self.temp.compare_variables(to_data_list(
                "files/comparaison/two_row_tab_varied_invalid_unknown_argument.json"
            ))


class Images(unittest.TestCase):

    temp = ootemplate.Template("unittest/files/comparaison/img_vars.odt", cnx, False)

    def test_valid(self):
        datas = to_data_list("files/comparaison/img_vars_valid.json")
        self.assertEqual(datas, self.temp.compare_variables(datas))

    def test_invalid_unknown_variable(self):
        with self.assertRaises(ootemplate.err.JsonUnknownVariable):
            self.temp.compare_variables(to_data_list("files/comparaison/img_vars_invalid_other_image.json"))

    def test_invalid_missing_variable(self):
        with self.assertRaises(ootemplate.err.JsonMissingRequiredVariable):
            self.temp.compare_variables(to_data_list("unittest/files/comparaison/img_vars_invalid_missing_img.json"))


if __name__ == '__main__':
    unittest.main()
