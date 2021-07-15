import unittest
import main as ootemplate

connexion = ootemplate.Connexion("localhost", "2002")


class Text(unittest.TestCase):

    def test_noformat(self):
        self.assertEqual({"gjerg": "", "jean": "", "aerhh": "", "rh": "", "aet": "", "h": ""},
                         ootemplate.Template("unittest/files/text_vars_noformat.odt", connexion, False).scan())

    def test_format(self):
        self.assertEqual({"gjerg": "", "jean": "", "aerhh": "", "rh": "", "aet": "", "h": ""},
                         ootemplate.Template("unittest/files/text_vars.odt", connexion, False).scan())

    def test_static_table(self):
        self.assertEqual({"var1": "", "var2": ""},
                         ootemplate.Template("unittest/files/static_tab.odt", connexion, False).scan())


class Images(unittest.TestCase):

    def test_one_image(self):
        self.assertEqual({"image": {"path": ""}},
                         ootemplate.Template("unittest/files/img_vars.odt", connexion, False).scan())


class Tables(unittest.TestCase):

    def test_multiple_row(self):
        self.assertEqual({"tab": [{"var1": "", "var2": ""}]},
                         ootemplate.Template("unittest/files/multiple_row_tab.odt", connexion, False).scan())

    def test_one_row_varied(self):
        self.assertEqual({"tab": [{"var": ""}]},
                         ootemplate.Template("unittest/files/one_row_tab_varied.odt", connexion, False).scan())

    def test_two_row_varied(self):
        self.assertEqual({"tab": [{"var1": ""}]},
                         ootemplate.Template("unittest/files/two_row_tab_varied.odt", connexion, False).scan())

    def test_invalid_var(self):
        with self.assertRaises(ootemplate.TemplateVariableNotInLastRow):
            ootemplate.Template("unittest/files/invalid_var_tab.odt", connexion, False).scan()

    def test_invalid_vars(self):
        with self.assertRaises(ootemplate.TemplateVariableNotInLastRow):
            ootemplate.Template("unittest/files/invalid_vars_tab.odt", connexion, False).scan()

    def test_two_tabs_varied(self):
        self.assertEqual({"tab": [{"var1": ""}], "tab2": [{"1": "", "2": "", "3": "", "4": "", "5": ""}]},
                         ootemplate.Template("unittest/files/two_tabs_varied.odt", connexion, False).scan())


if __name__ == '__main__':
    unittest.main()
