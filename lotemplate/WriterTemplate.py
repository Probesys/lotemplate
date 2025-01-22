"""
Copyright (C) 2023 Probesys


The classes used for document connexion and manipulation
"""

__all__ = (
    'Template',
)

from typing import Union
from sorcery import dict_of

import uno

from com.sun.star.beans import PropertyValue
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.style.BreakType import PAGE_AFTER

from . import errors


from .Template import Template

from lotemplate.Statement.ForStatement import ForStatement
from lotemplate.Statement.HtmlStatement import HtmlStatement
from lotemplate.Statement.IfStatement import IfStatement
from lotemplate.Statement.TextStatement import TextStatement
from lotemplate.Statement.TableStatement import TableStatement
from lotemplate.Statement.ImageStatement import ImageStatement
from lotemplate.Statement.CounterStatement import CounterManager

__all__ = (
    'WriterTemplate',
)


class WriterTemplate(Template):

    formats = {
            "odt": "writer8",
            "pdf": "writer_pdf_Export",
            "html": "HTML (StarWriter)",
            "docx": "Office Open XML Text",
            "txt": "Text (encoded)",
            'rtf': 'Rich Text Format'
        }

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

    def validDocType(self,doc):


        if not doc or not doc.supportsService('com.sun.star.text.GenericTextDocument'):
            if doc:
                doc.close(True)
            raise errors.TemplateError(
                'invalid_format',
                f"The given format ({self.file_name.split('.')[-1]!r}) is invalid, or the file is already open by "
                f"an other process (accepted formats: ODT, OTT, DOC, DOCX, HTML, RTF or TXT)",
                dict(format=self.file_name.split('.')[-1])
            )
        return doc


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

        #should_close = kwargs.get("should_close", False)

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
            self.close()
            raise errors.TemplateError(
                'duplicated_variable',
                f"The variable {duplicates[0]!r} is mentioned two times, but "
                f"for two different types: {first_type!r}, and {second_type!r}",
                dict_of(first_type, second_type, variable=duplicates[0])
            )

        return texts | tables | images | fors


    def fill(self, variables: dict[str, dict[str, Union[str, list[str]]]]) -> None:
        """
        Fills a template copy with the given values

        :param variables: the values to fill in the template
        :return: None
        """


        ###
        ### main calls
        ###
        ForStatement.for_replace(self.doc, variables)

        IfStatement.if_replace(self.doc, variables)

        for var, details in sorted(variables.items(), key=lambda s: -len(s[0])):
            if details['type'] == 'text':
                TextStatement.text_fill(self.doc, "$" + var, details['value'])
            elif details['type'] == 'image':
                ImageStatement.image_fill(self.doc, self.cnx.graphic_provider, "$" + var, details['value'])
            elif details['type'] == 'html':
                HtmlStatement.html_fill(template=self, doc=self.doc, variable="$" + var, value=details['value'])

        HtmlStatement.html_replace(template=self, doc=self.doc)

        TableStatement.tables_fill(self.doc, variables, '$', '&')

        CounterManager.counter_replace(self.doc)


    def page_break(self) -> None:
        """
        Add a page break to the document

        :return: None
        """

        if not self.doc:
            return

        cursor = self.doc.Text.createTextCursor()
        cursor.gotoEnd(False)
        cursor.collapseToEnd()
        cursor.BreakType = PAGE_AFTER
        self.doc.Text.insertControlCharacter(cursor, PARAGRAPH_BREAK, False)

