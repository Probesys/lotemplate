"""
Copyright (C) 2023 Probesys


LOTemplate Filler
~~~~~~~~~~~~~~~~~

A module for manipulate and fill libreoffice writer-like documents with given variables
Contains the two used classes, errors raised and some utils fonctions
"""


__title__ = 'LOTemplate Filler'
__version__ = '1.0'
__all__ = (
    'Connexion',
    'Template',
    'CalcTemplate',
    'WriterTemplate',
    'convert_to_datas_template',
    'is_network_based',
    'get_file_url',
    'TemplateFromExt',
    'start_multi_office',
    'randomConnexion',
)

from .connexion import Connexion
from .utils import convert_to_datas_template,is_network_based,get_file_url
from .Template import Template
from .WriterTemplate import WriterTemplate
from .CalcTemplate import CalcTemplate
from .lofunction import TemplateFromExt,start_multi_office,randomConnexion
