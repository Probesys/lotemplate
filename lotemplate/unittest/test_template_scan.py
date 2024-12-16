"""
Copyright (C) 2023 Probesys
"""

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
            {
                "gjerg": {"type": "text", "value": ""},
                "jean": {"type": "text", "value": ""},
                "aerhh": {"type": "text", "value": ""},
                "rh": {"type": "text", "value": ""},
                "aet": {"type": "text", "value": ""},
                "h": {"type": "text", "value": ""}
            },
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/text_vars_noformat.odt", cnx, False)).scan())
        doc.close()

    def test_format(self):
        self.assertEqual(
            {
                "gjerg": {"type": "text", "value": ""},
                "jean": {"type": "text", "value": ""},
                "aerhh": {"type": "text", "value": ""},
                "rh": {"type": "text", "value": ""},
                "aet": {"type": "text", "value": ""},
                "h": {"type": "text", "value": ""}
            },
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/text_vars.odt", cnx, False)).scan())
        doc.close()

    def test_text_var_in_header(self):
        self.assertEqual(
            {"my_var": {"type": "text", "value": ""}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/text_var_in_header.odt", cnx, False)).scan()
        )
        doc.close()

    def test_static_table(self):
        self.assertEqual(
            {"var1": {"type": "text", "value": ""}, "var2": {"type": "text", "value": ""}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/static_tab.odt", cnx, False)).scan()
        )
        doc.close()

    def test_function_variable(self):
        self.assertEqual(
            {"test(\"jean\")": {"type": "text", "value": ""}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/function_variable.odt", cnx, False)).scan()
        )
        doc.close()

    def test_for_variable(self):
        self.assertEqual(
            {"tutu": {"type": "array", "value": []}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/for.odt", cnx, False)).scan()
        )
        doc.close()

class Images(unittest.TestCase):

    def test_one_image(self):
        self.assertEqual(
            {"image": {"type": "image", "value": ""}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/img_vars.odt", cnx, False)).scan()
        )
        doc.close()

    def test_multiple_images(self):
        self.assertEqual(
            {
                "image1": {"type": "image", "value": ""},
                "image2": {"type": "image", "value": ""},
                "image3": {"type": "image", "value": ""}
            },
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/multiple_img_vars.odt", cnx, False)).scan()
        )
        doc.close()

class Ifs(unittest.TestCase):
    def test_no_endif(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/invalid_if_statement.odt", cnx, False)).scan()
        doc.close()


class Tables(unittest.TestCase):

    def test_multiple_row(self):
        self.assertEqual(
            {"var1": {"type": "table", "value": [""]}, "var2": {"type": "table", "value": [""]}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/multiple_row_tab.odt", cnx, False)).scan()
        )
        doc.close()

    def test_one_row_varied(self):
        self.assertEqual(
            {"var": {"type": "table", "value": [""]}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/one_row_tab_varied.odt", cnx, False)).scan()
        )
        doc.close()

    def test_two_row_varied(self):
        self.assertEqual(
            {"var1": {"type": "table", "value": [""]}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/two_row_tab_varied.odt", cnx, False)).scan()
        )
        doc.close()

    def test_invalid_var(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/invalid_var_tab.odt", cnx, False)).scan()
        doc.close()

    def test_invalid_vars(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/invalid_vars_tab.odt", cnx, False)).scan()
        doc.close()

    def test_for(self):
        self.assertEqual(
            {'tutu': {'type': 'array', 'value': []}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/for.odt", cnx, False)).scan()
        )
        doc.close()

    def test_for_missing_endfor(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/for_missing_endfor.odt", cnx, False)).scan()
        doc.close()

    def test_two_tabs_varied(self):
        self.assertEqual(
            {
                "var1": {"type": "table", "value": [""]},
                "1": {"type": "table", "value": [""]},
                "2": {"type": "table", "value": [""]},
                "3": {"type": "table", "value": [""]},
                "4": {"type": "table", "value": [""]},
                "5": {"type": "table", "value": [""]}
            },
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/two_tabs_varied.odt", cnx, False)).scan()
        )
        doc.close()

    def test_function_variable(self):
        self.assertEqual(
            {
                "test(&jean)": {"type": "table", "value": [""]},
                "test": {"type": "table", "value": [""]},
                "test2": {"type": "text", "value": ""},
            },
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/function_variable_tab.odt", cnx, False)).scan()
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
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/multiple_variables.odt", cnx, False)).scan())
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
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/multiple_pages.odt", cnx, False)).scan()
        )
        doc.close()

    def test_online_empty_doc(self):
        with self.assertRaises(ot.errors.FileNotFoundError):
            (doc := ot.WriterTemplate(
                "https://www.mtsac.edu/webdesign/accessible-docs/word/example03.docx", cnx, False))

    def test_invalid_path(self):
        with self.assertRaises(ot.errors.FileNotFoundError):
            ot.WriterTemplate("bfevg", cnx, True)

    def test_duplicated_variable(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/duplicated_variables.odt", cnx, False)).scan()
        doc.close()


class OtherFormats(unittest.TestCase):

    def test_ott(self):
        self.assertEqual(
            {
                "cell1": {"type": "table", "value": [""]},
                "cell2": {"type": "table", "value": [""]},
                "Nom": {"type": "text", "value": ""},
                "prenon": {"type": "text", "value": ""},
                "signature": {"type": "text", "value": ""},
                "photo": {"type": "image", "value": ""}
            },
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/format.ott", cnx, False)).scan()
        )
        doc.close()

    def test_docx(self):
        self.assertEqual(
            {
                "cell1": {"type": "text", "value": ""},
                "cell2": {"type": "text", "value": ""},
                "Nom": {"type": "text", "value": ""},
                "prenon": {"type": "text", "value": ""},
                "signature": {"type": "text", "value": ""},
                "photo": {"type": "image", "value": ""}
            },
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/format.docx", cnx, False)).scan()
        )
        doc.close()

    def test_text(self):
        self.assertEqual(
            {"signature": {"type": "text", "value": ""}},
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/format.txt", cnx, False)).scan()
        )
        doc.close()

    def test_html(self):
        self.assertEqual(
            {
                "cell1": {"type": "text", "value": ""},
                "cell2": {"type": "text", "value": ""},
                "Nom": {"type": "text", "value": ""},
                "prenon": {"type": "text", "value": ""},
                "signature": {"type": "text", "value": ""},
                "photo": {"type": "image", "value": ""}
            },
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/format.html", cnx, False)).scan()
        )
        doc.close()

    def test_html_without_endhtml(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/html_without_endhtml.odt", cnx, False)).scan()
            doc.close()


    def test_rtf(self):
        self.assertEqual(
            {
                "cell1": {"type": "text", "value": ""},
                "cell2": {"type": "text", "value": ""},
                "Nom": {"type": "text", "value": ""},
                "prenon": {"type": "text", "value": ""},
                "signature": {"type": "text", "value": ""}
            },
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/format.rtf", cnx, False)).scan()
        )
        doc.close()

    def test_for_inside_if(self):
        doc = ot.WriterTemplate("lotemplate/unittest/files/content/for_inside_if.odt", cnx, False)
        self.assertEqual(
            {
                'tata': {'type': 'text', 'value': ''},
                'tutu': {'type': 'array', 'value': []}
            },
            doc.scan()
        )
        # this is run twice to check if mutable scan_if can be run twice
        self.assertEqual(
            {
                'tata': {'type': 'text', 'value': ''},
                'tutu': {'type': 'array', 'value': []}
            },
            doc.scan()
        )
        doc.close()

    def test_if_too_many_endif(self):
        with self.assertRaises(ot.errors.TemplateError) as cm:
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/if_too_many_endif.odt", cnx, False)).scan()
            doc.close()
        self.assertEqual(cm.exception.code, "too_many_endif_found")

    def test_if_syntax_error(self):
        with self.assertRaises(ot.errors.TemplateError) as cm:
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/if_syntax_error.odt", cnx, False)).scan()
            doc.close()
        self.assertEqual(cm.exception.code, "syntax_error_in_if_statement")

    def test_for_syntax_error(self):
        with self.assertRaises(ot.errors.TemplateError) as cm:
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/for_syntax_error.odt", cnx, False)).scan()
            doc.close()
        self.assertEqual(cm.exception.code, "syntax_error_in_for_statement")

    def test_if_syntax_error_no_endif(self):
        with self.assertRaises(ot.errors.TemplateError) as cm:
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/if_syntax_error_no_endif.odt", cnx, False)).scan()
            doc.close()
        self.assertEqual(cm.exception.code, "no_endif_found")

    def test_invalid(self):
        with self.assertRaises(ot.errors.TemplateError):
            (doc := ot.WriterTemplate("lotemplate/unittest/files/templates/invalid_format.jpg", cnx, False)).scan()
            doc.close()


if __name__ == '__main__':
    unittest.main()
