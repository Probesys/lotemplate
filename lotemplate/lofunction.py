"""
Copyright (C) 2023 Probesys


The classes used for document connexion and manipulation
"""

__all__ = (
    'TemplateFromExt',
)

import os
from .WriterTemplate import *
from .CalcTemplate import *
from .connexion import *


def TemplateFromExt(file_path: str, cnx: Connexion, should_scan: bool):

        filename, file_extension = os.path.splitext(file_path)
        ods_ext=('.xls','.xlsx','.ods')
        if file_extension in ods_ext:
             document = CalcTemplate(file_path, cnx , should_scan)
        else:
             document = WriterTemplate(file_path, cnx , should_scan)
        return document

