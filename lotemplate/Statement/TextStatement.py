import re
from com.sun.star.lang import XComponent
from com.sun.star.beans import PropertyValue, UnknownPropertyException
import regex
from lotemplate.Statement.ForStatement import ForStatement
from lotemplate.Statement.TableStatement import TableStatement


class TextStatement:
    text_regex = regex.compile(r'\$(\w+(\(((?:\\.|.)*?)\))?)')
    def __init__(self, text_string):
        self.text_string = text_string

    def scan_text(doc: XComponent) -> dict[str, dict[str, str]]:
        """
        scan for text in the given doc

        :param doc: the document to scan
        :return: the scanned variables
        """

        raw_string = doc.getText().getString()
        matches = TextStatement.text_regex.finditer(raw_string)
        plain_vars = {}
        for var in matches:
            key_name = var[0][1:]
            # add to plain_vars if it doesn't matche ForStatement.foritem_regex
            if not re.search(ForStatement.forindex_regex, key_name, re.IGNORECASE):
                plain_vars[key_name] = {'type': 'text', 'value': ''}

        text_fields_vars = {}
        for page in doc.getDrawPages():
            for shape in page:
                try:
                    matches = TextStatement.text_regex.finditer(shape.String)
                except (AttributeError, UnknownPropertyException):
                    continue
                text_fields_vars = (text_fields_vars |
                                    {var.group(0)[1:]: {'type': 'text', 'value': ''} for var in matches})

        for var in TableStatement.scan_table(doc, get_list=True):
            if '$' + var in plain_vars:
                del plain_vars[var]

        for var in ForStatement.scan_for(doc):
            if var in plain_vars:
                del plain_vars[var]

        return plain_vars | text_fields_vars


    def text_fill(doc: XComponent, variable: str, value: str) -> None:
        """
        Fills all the text-related content

        :param doc: the document to fill
        :param variable: the variable to search
        :param value: the value to replace with
        :return: None
        """

        search = doc.createSearchDescriptor()
        search.SearchString = variable
        founded = doc.findAll(search)

        for x_found in founded:
            text = x_found.getText()
            cursor = text.createTextCursorByRange(x_found)
            cursor.String = value

        for page in doc.getDrawPages():
            for shape in page:
                if shape.getShapeType() == "com.sun.star.drawing.TextShape":
                    shape.String = shape.String.replace(variable, value)
