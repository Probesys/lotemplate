import unittest
import main as ootemplate
import test_json_convertion

cnx = ootemplate.Connexion("localhost", "2002")


def to_data_list(file: str) -> list:
    return [
        ootemplate.convert_to_datas_template(file, test_json_convertion.file_to_dict(file)),
        file,
    ]


class Text(unittest.TestCase):

    temp = ootemplate.Template("unittest/files/comparaison/text_vars.odt", cnx, True)

    def test_valid(self):
        self.temp.search_error(*to_data_list("files/comparaison/text_vars_valid.json"))

    def test_invalid_supplement_variable(self):
        with self.assertRaises(ootemplate.err.JsonUnknownVariable):
            self.temp.search_error(*to_data_list("files/comparaison/text_vars_invalid_variable.json"))

    def test_invalid_missing_variable(self):
        with self.assertRaises(ootemplate.err.JsonMissingRequiredVariable):
            self.temp.search_error(*to_data_list("files/comparaison/text_vars_invalid_missing_variable.json"))

    def test_invalid_incorrect_value(self):
        with self.assertRaises(ootemplate.err.JsonIncorrectValueType):
            self.temp.search_error(*to_data_list("files/comparaison/text_vars_incorrect_value.json"))

    temp_tab = ootemplate.Template("unittest/files/comparaison/static_tab.odt", cnx, True)

    def test_tab_valid(self):
        self.temp_tab.search_error(*to_data_list("files/comparaison/static_tab_valid.json"))


class Tables(unittest.TestCase):

    temp = ootemplate.Template("unittest/files/comparaison/two_row_tab_varied.odt", cnx, True)

    def test_valid(self):
        self.temp.search_error(*to_data_list("files/comparaison/two_row_tab_varied_valid.json"))

    def test_invalid_missing_variable(self):
        with self.assertRaises(ootemplate.err.JsonMissingRequiredVariable):
            self.temp.search_error(
                *to_data_list("files/comparaison/two_row_tab_varied_invalid_missing_argument_all_rows.json")
            )

    def test_invalid_unknown_variable(self):
        with self.assertRaises(ootemplate.err.JsonUnknownVariable):
            self.temp.search_error(*to_data_list("files/comparaison/two_row_tab_varied_invalid_unknown_argument.json"))


class Images(unittest.TestCase):

    temp = ootemplate.Template("unittest/files/comparaison/img_vars.odt", cnx, True)

    def test_valid(self):
        self.temp.search_error(*to_data_list("files/comparaison/img_vars_valid.json"))

    def test_invalid_unknown_variable(self):
        with self.assertRaises(ootemplate.err.JsonUnknownVariable):
            self.temp.search_error(*to_data_list("files/comparaison/img_vars_invalid_other_image.json"))

    def test_invalid_missing_variable(self):
        with self.assertRaises(ootemplate.err.JsonMissingRequiredVariable):
            self.temp.search_error(*to_data_list("files/comparaison/img_vars_invalid_missing_img.json"))


if __name__ == '__main__':
    unittest.main()
