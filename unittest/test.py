import unittest
import main as ootemplate


class TestTemplateScan(unittest.TestCase):

    connexion = ootemplate.Connexion("localhost", "2002")

    def test_text_vars(self):
        self.assertEqual(ootemplate.Template("unittest/files/text_vars.odt", self.connexion, True).scan(),
                         {"gjerg": None, "jean": None, "aerhh": None, "rh": None, "aet": None, "h": None})
        self.assertEqual(ootemplate.Template("unittest/files/text_vars_noformat.odt", self.connexion, True).scan(),
                         {"gjerg": None, "jean": None, "aerhh": None, "rh": None, "aet": None, "h": None})
        self.assertEqual(ootemplate.Template("unittest/files/static_tab.odt", self.connexion, True).scan(),
                         {"var1": None, "var2": None})

    def test_img_vars(self):
        self.assertEqual(ootemplate.Template("unittest/files/img_vars.odt", self.connexion, True).scan(),
                         {"image": {"path": None}})


if __name__ == '__main__':
    unittest.main()
