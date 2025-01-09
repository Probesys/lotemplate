import re
from com.sun.star.lang import XComponent
from com.sun.star.beans import PropertyValue, UnknownPropertyException
import regex
import pdb 

class CalcTextStatement:
    text_regex_str = r'\$(\w+(\(((?:\\.|.)*?)\))?)'
    text_regex = regex.compile(text_regex_str)
    table_regex_str = r'\&(\w+(\(((?:\\.|.)*?)\))?)'
    table_regex = regex.compile(table_regex_str)

    def __init__(self, text_string):
        self.text_string = text_string



    def scan(component: XComponent, get_table=False) -> dict[str, dict[str, str]]:
        """
        scan for text in the given doc

        :param doc: the document to scan
        :return: the scanned variables
        """ 
        if  component.getImplementationName()=="ScNamedRangeObj":
            #doc= component.getReferredCells().getSpreadsheet()
            doc=component.getReferredCells()
            regex_to_use=CalcTextStatement.table_regex_str
        else:
            doc=component
            regex_to_use=CalcTextStatement.text_regex_str

        plain_vars = {}
        search = doc.createReplaceDescriptor()
        search.SearchString = regex_to_use
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        founded = doc.findAll(search)
        var_table = {}
        if founded: 
            for x_found in founded:
                Arraytext = x_found.getDataArray()

                #cursor = text.createTextCursorByRange(x_found)
                for Array in  Arraytext:
                    for text in Array:
                        for result in re.findall(search.SearchString,text):
                            plain_vars[result[0]] = {'type': 'text', 'value': ''}
                            var_table[result[0]] = {'type': 'table', 'value':[]}


        return  var_table if get_table else plain_vars

    def fill(doc: XComponent, variable: str, value: str) -> None:
        """
        Fills all the text-related content

        :param doc: the document to fill
        :param variable: the variable to search
        :param value: the value to replace with
        :return: None
        """
        #pdb.set_trace()
        #print("var="+variable+" value="+value+" "+str(doc) )
        search = doc.createReplaceDescriptor()
        search.SearchString = variable
        search.ReplaceString = value
        founded = doc.replaceAll(search)



