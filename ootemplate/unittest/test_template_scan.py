import unittest
import ootemplate as ot

cnx = ot.Connexion("localhost", "2002")


class Text(unittest.TestCase):

    def test_noformat(self):
        self.assertEqual(
            {"gjerg": "", "jean": "", "aerhh": "", "rh": "", "aet": "", "h": ""},
            ot.Template("files/templates/text_vars_noformat.odt", cnx, False).scan()
        )

    def test_format(self):
        self.assertEqual(
            {"gjerg": "", "jean": "", "aerhh": "", "rh": "", "aet": "", "h": ""},
            ot.Template("files/templates/text_vars.odt", cnx, False).scan()
        )

    def test_static_table(self):
        self.assertEqual(
            {"var1": "", "var2": ""},
            ot.Template("files/templates/static_tab.odt", cnx, False).scan()
        )


class Images(unittest.TestCase):

    def test_one_image(self):
        self.assertEqual(
            {"image": [""]},
            ot.Template("files/templates/img_vars.odt", cnx, False).scan()
        )

    def test_multiple_images(self):
        self.assertEqual(
            {"image1": [""], "image2": [""], "image3": [""]},
            ot.Template("files/templates/multiple_img_vars.odt", cnx, False).scan()
        )


class Tables(unittest.TestCase):

    def test_multiple_row(self):
        self.assertEqual(
            {"tab": {"var1": [""], "var2": [""]}},
            ot.Template("files/templates/multiple_row_tab.odt", cnx, False).scan()
        )

    def test_one_row_varied(self):
        self.assertEqual(
            {"tab": {"var": [""]}},
            ot.Template("files/templates/one_row_tab_varied.odt", cnx, False).scan()
        )

    def test_two_row_varied(self):
        self.assertEqual(
            {"tab": {"var1": [""]}},
            ot.Template("files/templates/two_row_tab_varied.odt", cnx, False).scan()
        )

    def test_invalid_var(self):
        with self.assertRaises(ot.err.TemplateVariableNotInLastRow):
            ot.Template("files/templates/invalid_var_tab.odt", cnx, False).scan()

    def test_invalid_vars(self):
        with self.assertRaises(ot.err.TemplateVariableNotInLastRow):
            ot.Template("files/templates/invalid_vars_tab.odt", cnx, False).scan()

    def test_two_tabs_varied(self):
        self.assertEqual(
            {"tab": {"var1": [""]}, "tab2": {"1": [""], "2": [""], "3": [""], "4": [""], "5": [""]}},
            ot.Template("files/templates/two_tabs_varied.odt", cnx, False).scan()
        )


class Generic(unittest.TestCase):

    def test_multiple_variables(self):
        self.assertEqual(
            {
                "tab3": {"var1": [""], "var2": [""]},
                "tab1": {"cell1": [""], "cell2": [""]},
                "Nom": "",
                "prenon": "",
                "signature": "",
                "photo": [""],
                "static1": "",
                "static2": "",
                "static3": ""
            },
            ot.Template("files/templates/multiple_variables.odt", cnx, False).scan())

    def test_multiple_pages(self):
        self.assertEqual(
            {
                "tab3": {"var1": [""], "var2": [""]},
                "tab1": {"cell1": [""], "cell2": [""]},
                "Nom": "",
                "prenon": "",
                "signature": "",
                "photo": [""],
                "static1": "",
                "static2": "",
                "static3": "",
                "date": "",
                "lieu": ""
            },
            ot.Template("files/templates/multiple_pages.odt", cnx, False).scan()
        )

    def test_online_empty_doc(self):
        self.assertEqual(
            {},
            ot.Template("https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.docx", cnx, False).scan()
        )

    def test_invalid_path(self):
        with self.assertRaises(ot.err.FileNotFoundError):
            ot.Template("bfevg", cnx, True)

    def test_duplicated_variable(self):
        with self.assertRaises(ot.err.TemplateDuplicatedVariable):
            ot.Template("files/templates/duplicated_variables.odt", cnx, False).scan()


class OtherFormats(unittest.TestCase):

    def test_ott(self):
        self.assertEqual(
            {"tab1": {"cell1": [""], "cell2": [""]}, "Nom": "", "prenon": "", "signature": "", "photo": [""]},
            ot.Template("files/templates/format.ott", cnx, False).scan()
        )

    def test_docx(self):
        self.assertEqual(
            {"cell1": "", "cell2": "", "Nom": "", "prenon": "", "signature": "", "photo": [""]},
            ot.Template("files/templates/format.docx", cnx, False).scan()
        )

    def test_text(self):
        self.assertEqual(
            {"signature": ""},
            ot.Template("files/templates/format.txt", cnx, False).scan()
        )

    def test_html(self):
        self.assertEqual(
            {"cell1": "", "cell2": "", "Nom": "", "prenon": "", "signature": "", "photo": [""]},
            ot.Template("files/templates/format.html", cnx, False).scan()
        )

    def test_rtf(self):
        self.assertEqual(
            {"cell1": "", "cell2": "", "Nom": "", "prenon": "", "signature": ""},
            ot.Template("files/templates/format.rtf", cnx, False).scan()
        )

    def test_invalid(self):
        with self.assertRaises(ot.err.TemplateInvalidFormat):
            ot.Template("files/templates/invalid_format.jpg", cnx, False).scan()


if __name__ == '__main__':
    unittest.main()
