"""
Copyright (C) 2023 Probesys
"""
import unittest

import lotemplate as ot
from time import sleep
import subprocess
import filecmp
import os
import json
from lotemplate.unittest.test_function import *

cnx = start_office()


class Test_calc(unittest.TestCase):

    def test_cachedjson(self):
        cachejson="lotemplate/unittest/files/content/e89fbedb61af3994184da3e5340bd9e9-calc_variables.ods.json"
        if os.path.isfile(cachejson):
            os.remove(cachejson)
        ot.TemplateFromExt("lotemplate/unittest/files/templates/calc_variables.ods",cnx,True,json_cache_dir='lotemplate/unittest/files/content/')
        self.assertTrue(filecmp.cmp(cachejson,"lotemplate/unittest/files/content/e89fbedb61af3994184da3e5340bd9e9-calc_variables.ods.expected.json", shallow=False))


