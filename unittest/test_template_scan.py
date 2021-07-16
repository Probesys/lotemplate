import unittest
import main as ootemplate

connexion = ootemplate.Connexion("localhost", "2002")


class Text(unittest.TestCase):

    def test_noformat(self):
        self.assertEqual({"gjerg": "", "jean": "", "aerhh": "", "rh": "", "aet": "", "h": ""},
                         ootemplate.Template("unittest/files/templates/text_vars_noformat.odt",
                                             connexion, False).scan())

    def test_format(self):
        self.assertEqual({"gjerg": "", "jean": "", "aerhh": "", "rh": "", "aet": "", "h": ""},
                         ootemplate.Template("unittest/files/templates/text_vars.odt", connexion, False).scan())

    def test_static_table(self):
        self.assertEqual({"var1": "", "var2": ""},
                         ootemplate.Template("unittest/files/templates/static_tab.odt", connexion, False).scan())


class Images(unittest.TestCase):

    def test_one_image(self):
        self.assertEqual({"image": {"path": ""}},
                         ootemplate.Template("unittest/files/templates/img_vars.odt", connexion, False).scan())

    def test_multiple_images(self):
        self.assertEqual({"image1": {"path": ""}, "image2": {"path": ""}, "image3": {"path": ""}},
                         ootemplate.Template("unittest/files/templates/multiple_img_vars.odt", connexion, False).scan())


class Tables(unittest.TestCase):

    def test_multiple_row(self):
        self.assertEqual({"tab": [{"var1": "", "var2": ""}]},
                         ootemplate.Template("unittest/files/templates/multiple_row_tab.odt", connexion, False).scan())

    def test_one_row_varied(self):
        self.assertEqual({"tab": [{"var": ""}]},
                         ootemplate.Template("unittest/files/templates/one_row_tab_varied.odt",
                                             connexion, False).scan())

    def test_two_row_varied(self):
        self.assertEqual({"tab": [{"var1": ""}]},
                         ootemplate.Template("unittest/files/templates/two_row_tab_varied.odt",
                                             connexion, False).scan())

    def test_invalid_var(self):
        with self.assertRaises(ootemplate.err.TemplateVariableNotInLastRow):
            ootemplate.Template("unittest/files/templates/invalid_var_tab.odt", connexion, False).scan()

    def test_invalid_vars(self):
        with self.assertRaises(ootemplate.err.TemplateVariableNotInLastRow):
            ootemplate.Template("unittest/files/templates/invalid_vars_tab.odt", connexion, False).scan()

    def test_two_tabs_varied(self):
        self.assertEqual({"tab": [{"var1": ""}], "tab2": [{"1": "", "2": "", "3": "", "4": "", "5": ""}]},
                         ootemplate.Template("unittest/files/templates/two_tabs_varied.odt", connexion, False).scan())


class Generic(unittest.TestCase):

    def test_multiple_variables(self):
        self.assertEqual({"tab3": [{"var1": "", "var2": ""}], "tab1": [{"cell1": "", "cell2": ""}], "Nom": "",
                          "prenon": "", "signature": "", "photo": {"path": ""}, "static1": "", "static2": "",
                          "static3": ""},
                         ootemplate.Template("unittest/files/templates/multiple_variables.odt", connexion,
                                             False).scan())

    def test_multiple_pages(self):
        self.assertEqual({"tab3": [{"var1": "", "var2": ""}], "tab1": [{"cell1": "", "cell2": ""}], "Nom": "",
                          "prenon": "", "signature": "", "photo": {"path": ""}, "static1": "", "static2": "",
                          "static3": "", "date": "", "lieu": ""},
                         ootemplate.Template("unittest/files/templates/multiple_pages.odt", connexion, False).scan())

    def test_online_empty_doc(self):
        self.assertEqual({}, ootemplate.Template(
            "https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.docx", connexion, False).scan())

    def test_invalid_path(self):
        with self.assertRaises(Exception):
            ootemplate.Template("bfevg", connexion, True)


class OtherFormats(unittest.TestCase):

    def test_ott(self):
        self.assertEqual({"tab1": [{"cell1": "", "cell2": ""}], "Nom": "",
                          "prenon": "", "signature": "", "photo": {"path": ""}},
                         ootemplate.Template("unittest/files/templates/format.ott", connexion, False).scan())

    def test_docx(self):
        self.assertEqual({"cell1": "", "cell2": "", "Nom": "",
                          "prenon": "", "signature": "", "photo": {"path": ""}},
                         ootemplate.Template("unittest/files/templates/format.docx", connexion, False).scan())

    def test_text(self):
        self.assertEqual({"signature": ""},
                         ootemplate.Template("unittest/files/templates/format.txt", connexion, False).scan())

    def test_html(self):
        self.assertEqual({"cell1": "", "cell2": "", "Nom": "",
                          "prenon": "", "signature": "", "photo": {"path": ""}},
                         ootemplate.Template("unittest/files/templates/format.html", connexion, False).scan())

    def test_rtf(self):
        self.assertEqual({"cell1": "", "cell2": "", "Nom": "",
                          "prenon": "", "signature": ""},
                         ootemplate.Template("unittest/files/templates/format.rtf", connexion, False).scan())

    def test_invalid(self):
        with self.assertRaises(ootemplate.err.TemplateInvalidFormat):
            ootemplate.Template("unittest/files/templates/invalid_format.jpg", connexion, False).scan()


if __name__ == '__main__':
    unittest.main()
