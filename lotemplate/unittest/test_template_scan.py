import unittest
import lotemplate as ot
from time import sleep
import subprocess

subprocess.call(f'soffice "--accept=socket,host=localhost,port=2002;urp;StarOffice.ServiceManager" &', shell=True)
sleep(2)
cnx = ot.Connexion("localhost", "2002")


class Text(unittest.TestCase):

    def test_noformat(self):
        self.assertEqual(
            {"gjerg": {"type": "text", "value": ""}, "jean": {"type": "text", "value": ""}, "aerhh": {"type": "text", "value": ""}, "rh": {"type": "text", "value": ""}, "aet": {"type": "text", "value": ""}, "h": {"type": "text", "value": ""}},
            (doc := ot.Template("files/templates/text_vars_noformat.odt", cnx, False)).scan()
        )
        doc.close()

    def test_format(self):
        self.assertEqual(
            {"gjerg": {"type": "text", "value": ""}, "jean": {"type": "text", "value": ""}, "aerhh": {"type": "text", "value": ""}, "rh": {"type": "text", "value": ""}, "aet": {"type": "text", "value": ""}, "h": {"type": "text", "value": ""}},
            (doc := ot.Template("files/templates/text_vars.odt", cnx, False)).scan()
        )
        doc.close()

    def test_static_table(self):
        self.assertEqual(
            {"var1": {"type": "text", "value": ""}, "var2": {"type": "text", "value": ""}},
            (doc := ot.Template("files/templates/static_tab.odt", cnx, False)).scan()
        )
        doc.close()

    def test_function_variable(self):
        self.assertEqual(
            {"test(\"jean\")": {"type": "text", "value": ""}},
            (doc := ot.Template("files/templates/function_variable.odt", cnx, False)).scan()
        )
        doc.close()


class Images(unittest.TestCase):

    def test_one_image(self):
        self.assertEqual(
            {"image": {"type": "image", "value": ""}},
            (doc := ot.Template("files/templates/img_vars.odt", cnx, False)).scan()
        )
        doc.close()

    def test_multiple_images(self):
        self.assertEqual(
            {"image1": {"type": "image", "value": ""}, "image2": {"type": "image", "value": ""}, "image3": {"type": "image", "value": ""}},
            (doc := ot.Template("files/templates/multiple_img_vars.odt", cnx, False)).scan()
        )
        doc.close()


class Tables(unittest.TestCase):

    def test_multiple_row(self):
        self.assertEqual(
            {"var1": {"type": "table", "value": [""]}, "var2": {"type": "table", "value": [""]}},
            (doc := ot.Template("files/templates/multiple_row_tab.odt", cnx, False)).scan()
        )
        doc.close()

    def test_one_row_varied(self):
        self.assertEqual(
            {"var": {"type": "table", "value": [""]}},
            (doc := ot.Template("files/templates/one_row_tab_varied.odt", cnx, False)).scan()
        )
        doc.close()

    def test_two_row_varied(self):
        self.assertEqual(
            {"var1": {"type": "table", "value": [""]}},
            (doc := ot.Template("files/templates/two_row_tab_varied.odt", cnx, False)).scan()
        )
        doc.close()

    def test_invalid_var(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.Template("files/templates/invalid_var_tab.odt", cnx, False)).scan()
        doc.close()

    def test_invalid_vars(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.Template("files/templates/invalid_vars_tab.odt", cnx, False)).scan()
        doc.close()

    def test_two_tabs_varied(self):
        self.assertEqual(
            {"var1": {"type": "table", "value": [""]}, "1": {"type": "table", "value": [""]}, "2": {"type": "table", "value": [""]}, "3": {"type": "table", "value": [""]}, "4": {"type": "table", "value": [""]}, "5": {"type": "table", "value": [""]}},
            (doc := ot.Template("files/templates/two_tabs_varied.odt", cnx, False)).scan()
        )
        doc.close()


class Generic(unittest.TestCase):

    def test_multiple_variables(self):
        self.assertEqual(
            {
                "var1": {"type": "table", "value": [""]},
                "var2": {"type": "table", "value": [""]},
                "cell1": {"type": "table", "value": [""]},
                "cell2": {"type": "table", "value": [""]},
                "Nom": {"type": "text", "value": ""},
                "prenon": {"type": "text", "value": ""},
                "signature": {"type": "text", "value": ""},
                "photo": {"type": "image", "value": ""},
                "static1": {"type": "text", "value": ""},
                "static2": {"type": "text", "value": ""},
                "static3": {"type": "text", "value": ""}
            },
            (doc := ot.Template("files/templates/multiple_variables.odt", cnx, False)).scan())
        doc.close()

    def test_multiple_pages(self):
        self.assertEqual(
            {
                "var1": {"type": "table", "value": [""]},
                "var2": {"type": "table", "value": [""]},
                "cell1": {"type": "table", "value": [""]},
                "cell2": {"type": "table", "value": [""]},
                "Nom": {"type": "text", "value": ""},
                "prenon": {"type": "text", "value": ""},
                "signature": {"type": "text", "value": ""},
                "photo": {"type": "image", "value": ""},
                "static1": {"type": "text", "value": ""},
                "static2": {"type": "text", "value": ""},
                "static3": {"type": "text", "value": ""},
                "date": {"type": "text", "value": ""},
                "lieu": {"type": "text", "value": ""}
            },
            (doc := ot.Template("files/templates/multiple_pages.odt", cnx, False)).scan()
        )
        doc.close()

    def test_online_empty_doc(self):
        self.assertEqual(
            {},
            (doc := ot.Template("https://www.mtsac.edu/webdesign/accessible-docs/word/example03.docx", cnx, False)).scan()
        )
        doc.close()

    def test_invalid_path(self):
        with self.assertRaises(ot.errors.FileNotFoundError):
            ot.Template("bfevg", cnx, True)

    def test_duplicated_variable(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.Template("files/templates/duplicated_variables.odt", cnx, False)).scan()
        doc.close()


class OtherFormats(unittest.TestCase):

    def test_ott(self):
        self.assertEqual(
            {"cell1": {"type": "table", "value": [""]}, "cell2": {"type": "table", "value": [""]}, "Nom": {"type": "text", "value": ""}, "prenon": {"type": "text", "value": ""}, "signature": {"type": "text", "value": ""}, "photo": {"type": "image", "value": ""}},
            (doc := ot.Template("files/templates/format.ott", cnx, False)).scan()
        )
        doc.close()

    def test_docx(self):
        self.assertEqual(
            {"cell1": {"type": "text", "value": ""}, "cell2": {"type": "text", "value": ""}, "Nom": {"type": "text", "value": ""}, "prenon": {"type": "text", "value": ""}, "signature": {"type": "text", "value": ""}, "photo": {"type": "image", "value": ""}},
            (doc := ot.Template("files/templates/format.docx", cnx, False)).scan()
        )
        doc.close()

    def test_text(self):
        self.assertEqual(
            {"signature": {"type": "text", "value": ""}},
            (doc := ot.Template("files/templates/format.txt", cnx, False)).scan()
        )
        doc.close()

    def test_html(self):
        self.assertEqual(
            {"cell1": {"type": "text", "value": ""}, "cell2": {"type": "text", "value": ""}, "Nom": {"type": "text", "value": ""}, "prenon": {"type": "text", "value": ""}, "signature": {"type": "text", "value": ""}, "photo": {"type": "image", "value": ""}},
            (doc := ot.Template("files/templates/format.html", cnx, False)).scan()
        )
        doc.close()

    def test_rtf(self):
        self.assertEqual(
            {"cell1": {"type": "text", "value": ""}, "cell2": {"type": "text", "value": ""}, "Nom": {"type": "text", "value": ""}, "prenon": {"type": "text", "value": ""}, "signature": {"type": "text", "value": ""}},
            (doc := ot.Template("files/templates/format.rtf", cnx, False)).scan()
        )
        doc.close()

    def test_invalid(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.Template("files/templates/invalid_format.jpg", cnx, False)).scan()
            doc.close()


if __name__ == '__main__':
    unittest.main()
