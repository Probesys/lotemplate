import re
from com.sun.star.lang import XComponent
from com.sun.star.beans import PropertyValue, UnknownPropertyException
import regex
from lotemplate.Statement.ForStatement import ForStatement
from lotemplate.Statement.TableStatement import TableStatement
#import pdb 

class CalcTextStatement:
    text_regex_as_string = r'\$(\w+(\(((?:\\.|.)*?)\))?)'
    text_regex = regex.compile(text_regex_as_string)

    def __init__(self, text_string):
        self.text_string = text_string



    def scan_text(doc: XComponent) -> dict[str, dict[str, str]]:
        """
        scan for text in the given doc

        :param doc: the document to scan
        :return: the scanned variables
        """


        plain_vars = {}
        search = doc.createReplaceDescriptor()
        search.SearchString = CalcTextStatement.text_regex_as_string
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        founded = doc.findAll(search)
        simple_var_list = []
        for x_found in founded:
            Arraytext = x_found.getDataArray()
            #cursor = text.createTextCursorByRange(x_found)
            for text in  Arraytext:

                for result in re.findall(search.SearchString,text[0]):
                    plain_vars[result[0]] = {'type': 'text', 'value': ''}




        return plain_vars

    def text_fill(doc: XComponent, variable: str, value: str) -> None:
        """
        Fills all the text-related content

        :param doc: the document to fill
        :param variable: the variable to search
        :param value: the value to replace with
        :return: None
        """

        search = doc.createReplaceDescriptor()
        search.SearchString = variable
        search.ReplaceString = value
        founded = doc.replaceAll(search)


