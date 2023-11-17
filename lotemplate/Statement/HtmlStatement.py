import re
from sorcery import dict_of
import lotemplate.errors as errors
from com.sun.star.lang import XComponent

class HtmlStatement:
    """
    Class representing an html statement in a template libreoffice
    """
    start_regex = r'\[\s*html\s*\]'
    end_regex = r'\[\s*endhtml\s*\]'
    def __init__(self, html_string):
        self.html_string = html_string

    def scan_html(doc: XComponent) -> None:
        """
        scan html statement.

        We verify that
        - there is and endhtml for each html statement
        """

        def scan_single_html(local_x_found) -> None:
            """
            scan for a single for statement
            """
            html_statement = HtmlStatement(local_x_found.getString())
            position_in_text = len(html_statement.html_string)
            text = local_x_found.getText()
            cursor = text.createTextCursorByRange(local_x_found)
            while True:
                if not cursor.goRight(1, True):
                    raise errors.TemplateError(
                        'no_endhtml_found',
                        f"The statement {html_statement.html_string} has no endhtml",
                        dict_of(html_statement.html_string)
                    )
                position_in_text = position_in_text + 1
                selected_string = cursor.String
                match = re.search(HtmlStatement.end_regex, selected_string, re.IGNORECASE)
                if match is not None:
                    break

        search = doc.createSearchDescriptor()
        search.SearchString = HtmlStatement.start_regex
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        x_found = doc.findFirst(search)

        while x_found is not None:
            scan_single_html(x_found)
            x_found = doc.findNext(x_found.End, search)


    def html_replace(template, doc: XComponent) -> None:
        """
        Replace the content inside [html] and [endhtml] with a pasted html code inside the doc
        """

        def compute_html(doc, local_x_found):
            html_statement = HtmlStatement(local_x_found.getString())
            endhtml_search = doc.createSearchDescriptor()
            endhtml_search.SearchString = HtmlStatement.end_regex
            endhtml_search.SearchRegularExpression = True
            endhtml_search.SearchCaseSensitive = False
            x_found_endhtml = doc.findNext(local_x_found.End, endhtml_search)
            if x_found_endhtml is None:
                cursor = local_x_found.getText().createTextCursorByRange(local_x_found)
                raise errors.TemplateError(
                    'no_endhtml_found',
                    f"The statement [html] has no endhtml",
                    dict_of(cursor.String)
                )

            html_text = local_x_found.getText()
            endhtml_text = x_found_endhtml.getText()
            html_cursor = html_text.createTextCursorByRange(local_x_found)
            endhtml_cursor = endhtml_text.createTextCursorByRange(x_found_endhtml)
            content_cursor = html_text.createTextCursorByRange(local_x_found.End)
            content_cursor.gotoRange(x_found_endhtml.Start, True)
            html_string = content_cursor.String
            html_cursor.String = ''
            endhtml_cursor.String = ''
            content_cursor.String = ''
            template.pasteHtml(html_string, content_cursor)

        # main of for_replace
        search = doc.createSearchDescriptor()
        search.SearchString = HtmlStatement.start_regex
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        x_found = doc.findFirst(search)
        while x_found is not None:
            compute_html(doc, x_found)
            x_found = doc.findNext(x_found.End, search)

    def html_fill(template, doc: XComponent, variable: str, value: str) -> None:
        """
        Fills all the html-related content (contents of type "html" in the json file)

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
            cursor.String = ""
            template.pasteHtml(value, cursor)

        for page in doc.getDrawPages():
            for shape in page:
                if shape.getShapeType() == "com.sun.star.drawing.TextShape":
                    shape.String = shape.String.replace(variable, value)
                    # we wanted to use the pasteHtml function, but it doesn't work in a shape
                    # cursor = shape.createTextCursor()
                    # oldString = cursor.String
                    # self.pasteHtml(oldString.replace(variable, value), cursor)
