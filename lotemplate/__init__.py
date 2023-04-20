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
    'errors',
    'convert_to_datas_template',
    'is_network_based',
    'get_file_url',
)

from .errors import *
from .utils import *
from .classes import *

