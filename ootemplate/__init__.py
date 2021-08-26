"""
OOTemplate Filler
~~~~~~~~~~~~~~~~~

A module for manipulate and fill openoffice writter-like documents with given variables
Contains the two used classes, errors raised and some utils fonctions
"""


__title__ = 'OOTemplate Filler'
__version__ = '1.0'
__all__ = (
    'Connexion',
    'Template',
    'err',
    'convert_to_datas_template',
    'is_network_based',
    'get_file_url',
    'get_files_json',
    'get_normized_json',
)

from .exceptions import *
from .utils import *
from .classes import *

