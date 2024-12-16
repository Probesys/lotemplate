"""
Copyright (C) 2023 Probesys


The classes used for document connexion and manipulation
"""

__all__ = (
    'Template',
)

import os
from typing import Union
from sorcery import dict_of

import uno
import unohelper
from com.sun.star.beans import PropertyValue
from com.sun.star.io import IOException
from com.sun.star.lang import IllegalArgumentException, DisposedException
from com.sun.star.connection import NoConnectException
from com.sun.star.uno import RuntimeException
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.style.BreakType import PAGE_AFTER

from . import errors
from . import Connexion 
from .utils import *

from lotemplate.Statement.ForStatement import ForStatement
from lotemplate.Statement.HtmlStatement import HtmlStatement
from lotemplate.Statement.IfStatement import IfStatement
from lotemplate.Statement.TextStatement import TextStatement
from lotemplate.Statement.TableStatement import TableStatement
from lotemplate.Statement.ImageStatement import ImageStatement
from lotemplate.Statement.CounterStatement import CounterManager
import uuid
import shutil
import pdb


class Template:

    TMPDIR='tmpfile'

    formats =  {}


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        return str(self.file_name)

    def __repr__(self):
        return repr(self.file_url)

    def __getitem__(self, item):
        return self.variables[item] if self.variables else None

    def open_doc_from_url(self):
        try:
            doc = self.cnx.desktop.loadComponentFromURL(self.file_url, "_blank", 0, ())
        except DisposedException as e:
            self.close()
            raise errors.UnoException(
                'bridge_exception',
                f"The connection bridge on '{self.cnx.host}:{self.cnx.port}' crashed on file opening."
                f"Please restart the soffice process. For more informations on what caused this bug and how to avoid "
                f"it, please read the README file, section 'Unsolvable Problems'.",
                dict_of(self.cnx.host, self.cnx.port)
            ) from e
        except IllegalArgumentException:
            self.close()
            raise errors.FileNotFoundError(
                'file_not_found',
                f"the given file does not exist or has not been found (file {self.file_path!r})",
                dict_of(self.file_path)
            ) from None
        except RuntimeException as e:
            self.close()
            raise errors.UnoException(
                'connection_closed',
                f"The previously established connection with the soffice process on '{self.cnx.host}:{self.cnx.port}' "
                f"has been closed, or ran into an unknown error. Please restart the soffice process, and retry.",
                dict_of(self.cnx.host, self.cnx.port)
            ) from e
        self.validDocType(doc)
        return doc

    def validDocType(self,doc):
           pass

    def __init__(self, file_path: str, cnx: Connexion, should_scan: bool):
        """
        An object representing a LibreOffice/OpenOffice template that you can fill, scan, export and more

        :param file_path: the path of the document
        :param cnx: the connection object to the bridge
        :param should_scan: indicates if the document should be scanned at initialisation
        """
        if os.path.exists(file_path):
            self.cnx = cnx
            self.file_name = file_path.split("/")[-1]
            self.file_dir = "/".join(file_path.split("/")[:-1])
            self.file_path = file_path
            self.file_tmp_name=str(uuid.uuid4())+'_'+self.file_name
            self.tmp_file=Template.TMPDIR+"/"+self.file_tmp_name

            shutil.copy(file_path, self.tmp_file)

            self.file_url = get_file_url(self.tmp_file)
            self.variables = None
            self.doc = None
            self.doc = self.open_doc_from_url()
            self.variables = self.scan(should_close=True) if should_scan else None
        else:
            raise errors.FileNotFoundError(
                'file_not_found',
                f"the given file does not exist or has not been found (file {file_path!r})",
                dict_of(file_path))

    def scan(self, **kwargs) -> dict[str: dict[str, Union[str, list[str]]]]:
        """
        scans the variables contained in the template. Supports text, tables and images

        :return: list containing all the variables founded in the template
        """

        pass

    def search_error(self, json_vars: dict[str, dict[str, Union[str, list[str]]]]) -> None:
        """
        find out which variable is a problem, and raise the required error

        :param json_vars: the given json variables
        :return: None
        """
        if json_vars == self.variables:
            return

        json_missing = [key for key in set(self.variables) - set(json_vars)]
        if json_missing:
            raise errors.JsonComparaisonError(
                'missing_required_variable',
                f"The variable {json_missing[0]!r}, present in the template, "
                f"isn't present in the json.",
                dict(variable=json_missing[0])
            )

        # when parsing the template, we assume that all vars are of type text. But it can also be of type html.
        # So we check if types are equals or if type in json is "html" while type in template is "text"
        json_incorrect = [key for key in self.variables if (json_vars[key]['type'] != self.variables[key]['type']) and (json_vars[key]['type'] != "html" or self.variables[key]['type']!="text")]
        if json_incorrect:
            raise errors.JsonComparaisonError(
                'incorrect_value_type',
                f"The variable {json_incorrect[0]!r} should be of type "
                f"{self.variables[json_incorrect[0]]['type']!r}, like in the template, but is of type "
                f"{json_vars[json_incorrect[0]]['type']!r}",
                dict(variable=json_incorrect[0], actual_variable_type=json_vars[json_incorrect[0]]['type'],
                     expected_variable_type=self.variables[json_incorrect[0]]['type'])
            )

        template_missing = [key for key in set(json_vars) - set(self.variables)]
        json_vars_without_template_missing = {key: json_vars[key] for key in json_vars if key not in template_missing}
        if json_vars_without_template_missing == self.variables:
            return

    def fill(self, variables: dict[str, dict[str, Union[str, list[str]]]]) -> None:
            pass

    def close(self) -> None:
        """
        close the template

        :return: None
        """

        if not self:
            return
        if self.doc:
            self.doc.close(True)
        try:
            os.remove(self.tmp_file)
            os.remove(Template.TMPDIR+ "/.~lock." + self.file_tmp_name + "#")
        except FileNotFoundError:
            pass

    def export(self, filename: str, dirname=None, no_uid=None )  -> Union[str, None]:
        """
        Exports the newly generated document, if any.

        :param name: the path/name with file extension of the file to export.
        file type is automatically deducted from it.
        :return: the full path of the exported document, or None if there is no document to export
        """
        file_type = filename.split(".")[-1]
        if no_uid:
            path = os.getcwd() + "/" + dirname +  '/' + filename
        else:
            path = os.getcwd() + "/" + dirname +  '/' + str(uuid.uuid4()) +filename
        url = unohelper.systemPathToFileUrl(path)

        # list of available convert filters
        # cf https://help.libreoffice.org/latest/he/text/shared/guide/convertfilters.html
        try:
            self.doc.storeToURL(url, (PropertyValue("FilterName", 0, self.formats[file_type], 0),))
        except KeyError:
            raise errors.ExportError('invalid_format',
                                     f"Invalid export format {file_type!r}.", dict_of(file_type)) from None
        except IOException as error:

            raise errors.ExportError(
                'unknown_error',
                f"Unable to save document to {path!r} : error {error.value!r}",
                dict_of(path, error)
            ) from error

        return path


