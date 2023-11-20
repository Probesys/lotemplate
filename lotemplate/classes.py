"""
Copyright (C) 2023 Probesys


The classes used for document connexion and manipulation
"""

__all__ = (
    'Connexion',
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
from .utils import *

from lotemplate.Statement.ForStatement import ForStatement
from lotemplate.Statement.HtmlStatement import HtmlStatement
from lotemplate.Statement.IfStatement import IfStatement
from lotemplate.Statement.TextStatement import TextStatement
from lotemplate.Statement.TableStatement import TableStatement
from lotemplate.Statement.ImageStatement import ImageStatement
from lotemplate.Statement.CounterStatement import CounterManager

class Connexion:

    def __repr__(self):
        return (
            f"<Connexion object :'host'={self.host!r}, 'port'={self.port!r}, "
            f"'local_ctx'={self.local_ctx!r}, 'ctx'={self.local_ctx!r}, 'desktop'={self.desktop!r}, "
            f"'graphic_provider'={self.graphic_provider!r}>"
        )

    def __str__(self):
        return f"Connexion host {self.host}, port {self.port}"

    def __init__(self, host: str, port: str):
        """
        An object representing the connexion between the script and the LibreOffice/OpenOffice processus

        :param host: the address of the host to connect to
        :param port: the host port to connect to
        """

        self.host = host
        self.port = port
        self.local_ctx = uno.getComponentContext()
        try:
            self.ctx = self.local_ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", self.local_ctx
            ).resolve(f"uno:socket,host={host},port={port};urp;StarOffice.ComponentContext")
        except (NoConnectException, RuntimeException) as e:
            raise errors.UnoException(
                'connection_error',
                f"Couldn't find/connect to the soffice process on \'{host}:{port}\'. "
                f"Make sure the soffice process is correctly running with correct host and port informations. "
                f"Read the README file, section 'Executing the script' for more informations about how to "
                f"run the script.", dict_of(host, port)
            ) from e
        self.desktop = self.ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self.ctx)
        self.graphic_provider = self.ctx.ServiceManager.createInstance('com.sun.star.graphic.GraphicProvider')

    def restart(self) -> None:
        """
        Restart the connexion

        :return: None
        """

        self.__init__(self.host, self.port)

class Template:

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

        if not doc or not doc.supportsService('com.sun.star.text.GenericTextDocument'):
            self.close()
            raise errors.TemplateError(
                'invalid_format',
                f"The given format ({self.file_name.split('.')[-1]!r}) is invalid, or the file is already open by "
                f"an other process (accepted formats: ODT, OTT, DOC, DOCX, HTML, RTF or TXT)",
                dict(format=self.file_name.split('.')[-1])
            )
        return doc


    def __init__(self, file_path: str, cnx: Connexion, should_scan: bool):
        """
        An object representing a LibreOffice/OpenOffice template that you can fill, scan, export and more

        :param file_path: the path of the document
        :param cnx: the connection object to the bridge
        :param should_scan: indicates if the document should be scanned at initialisation
        """

        self.cnx = cnx
        self.file_name = file_path.split("/")[-1]
        self.file_dir = "/".join(file_path.split("/")[:-1])
        self.file_path = file_path
        self.file_url = get_file_url(file_path)
        self.new = None
        self.variables = None
        self.doc = None
        try:
            os.remove(self.file_dir + "/.~lock." + self.file_name + "#")
        except FileNotFoundError:
            pass
        self.doc = self.open_doc_from_url()
        self.variables = self.scan(should_close=True) if should_scan else None

    def pasteHtml(self, html_string, cursor):
        """
        copy the html string as html at the location of the cursor
        :param html_string:
        :param cursor:
        :return:
        """
        # horrible hack : there is a bug with the "paste HTML" function of libreoffice, so we have to add
        # a &nbsp; at the beginning of the string to make it work. Without that, the first element of a list
        # <ul><li>...</li></ul> is displayed without the bullet point. This is the less visible workaround I found.
        html_string = '&nbsp;' + html_string
        input_stream = self.cnx.ctx.ServiceManager.createInstanceWithContext("com.sun.star.io.SequenceInputStream",
                                                                             self.cnx.ctx)
        input_stream.initialize((uno.ByteSequence(html_string.encode()),))
        prop1 = PropertyValue()
        prop1.Name = "FilterName"
        prop1.Value = "HTML (StarWriter)"
        prop2 = PropertyValue()
        prop2.Name = "InputStream"
        prop2.Value = input_stream
        cursor.insertDocumentFromURL("private:stream", (prop1, prop2))

    def scan(self, **kwargs) -> dict[str: dict[str, Union[str, list[str]]]]:
        """
        scans the variables contained in the template. Supports text, tables and images

        :return: list containing all the variables founded in the template
        """

        should_close = kwargs.get("should_close", False)

        texts = TextStatement.scan_text(self.doc)
        # we use another document for if statement scanning because it modifies the file
        IfStatement.scan_if(template = self)
        tables = TableStatement.scan_table(self.doc)
        images = ImageStatement.scan_image(self.doc)
        fors = ForStatement.scan_for(self.doc)
        HtmlStatement.scan_html(self.doc)
        CounterManager.scan_counter(self.doc)

        variables_list = list(texts.keys()) + list(tables.keys()) + list(images.keys()) + list(fors.keys())
        duplicates = [variable for variable in variables_list if variables_list.count(variable) > 1]

        if duplicates:
            first_type = "text" if duplicates[0] in texts.keys() else "image"
            second_type = "table" if duplicates[0] in tables.keys() else "image"
            if should_close:
                self.close()
            raise errors.TemplateError(
                'duplicated_variable',
                f"The variable {duplicates[0]!r} is mentioned two times, but "
                f"for two different types: {first_type!r}, and {second_type!r}",
                dict_of(first_type, second_type, variable=duplicates[0])
            )

        return texts | tables | images | fors

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
        """
        Fills a template copy with the given values

        :param variables: the values to fill in the template
        :return: None
        """

        if self.new:
            self.new.dispose()
            self.new.close(True)

        try:
            self.new = (self.cnx.desktop.loadComponentFromURL(self.file_url, "_blank", 0, ()))
        except DisposedException as e:
            raise errors.UnoException(
                'bridge_exception',
                f"The connection bridge on '{self.cnx.host}:{self.cnx.port}' crashed on file opening."
                f"Please restart the soffice process. For more informations on what caused this bug and how to "
                f"avoid it, please read the README file, section 'Unsolvable Problems'.",
                dict_of(self.cnx.host, self.cnx.port)
            ) from e
        except RuntimeException as e:
            raise errors.UnoException(
                'connection_closed',
                f"The previously established connection with the soffice process on "
                f"'{self.cnx.host}:{self.cnx.port}' has been closed, or ran into an unknown error. "
                f"Please restart the soffice process, and retry.",
                dict_of(self.cnx.host, self.cnx.port)
            ) from e

        ###
        ### main calls
        ###
        ForStatement.for_replace(self.new, variables)

        IfStatement.if_replace(self.new, variables)

        for var, details in sorted(variables.items(), key=lambda s: -len(s[0])):
            if details['type'] == 'text':
                TextStatement.text_fill(self.new, "$" + var, details['value'])
            elif details['type'] == 'image':
                ImageStatement.image_fill(self.new, self.cnx.graphic_provider, "$" + var, details['value'])
            elif details['type'] == 'html':
                HtmlStatement.html_fill(template=self, doc=self.new, variable="$" + var, value=details['value'])

        HtmlStatement.html_replace(template=self, doc=self.new)

        TableStatement.tables_fill(self.new, variables, '$', '&')

        CounterManager.counter_replace(self.new)

    def export(self, name: str, should_replace=False) -> Union[str, None]:
        """
        Exports the newly generated document, if any.

        :param should_replace: precise if the exported file should replace the fils with the same name
        :param name: the path/name with file extension of the file to export.
        file type is automatically deducted from it.
        :return: the full path of the exported document, or None if there is no document to export
        """

        if not self.new:
            return

        file_type = name.split(".")[-1]
        path = os.getcwd() + "/" + name if name != '/' else name
        path_without_num = path
        if not should_replace:
            i = 1
            while os.path.isfile(path):
                path = path_without_num[:-(len(file_type) + 1)] + f"_{i}." + file_type
                i += 1

        url = unohelper.systemPathToFileUrl(path)

        # list of available convert filters
        # cf https://help.libreoffice.org/latest/he/text/shared/guide/convertfilters.html
        formats = {
            "odt": "writer8",
            "pdf": "writer_pdf_Export",
            "html": "HTML (StarWriter)",
            "docx": "Office Open XML Text",
            "txt": "Text (encoded)",
            'rtf': 'Rich Text Format'
        }

        try:
            self.new.storeToURL(url, (PropertyValue("FilterName", 0, formats[file_type], 0),))

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

    def close(self) -> None:
        """
        close the template

        :return: None
        """

        if not self:
            return
        if self.new:
            self.new.dispose()
            self.new.close(True)
            self.new = None
        if self.doc:
            self.doc.dispose()
            self.doc.close(True)
        try:
            os.remove(self.file_dir + "/.~lock." + self.file_name + "#")
        except FileNotFoundError:
            pass

    def page_break(self) -> None:
        """
        Add a page break to the document

        :return: None
        """

        if not self.new:
            return

        cursor = self.new.Text.createTextCursor()
        cursor.gotoEnd(False)
        cursor.collapseToEnd()
        cursor.BreakType = PAGE_AFTER
        self.new.Text.insertControlCharacter(cursor, PARAGRAPH_BREAK, False)
