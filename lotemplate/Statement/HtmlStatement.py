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
            text = local_x_found.getText()
            cursor = text.createTextCursorByRange(local_x_found)
            while True:
                if not cursor.goRight(1, True):
                    raise errors.TemplateError(
                        'no_endhtml_found',
                        f"The statement [html] has no endhtml",
                        dict_of(html_statement.html_string)
                    )

                selected_string = cursor.String
                match = re.search(HtmlStatement.end_regex, selected_string, re.IGNORECASE)
                if match is not None:
                    break
            cursor.String = ''
            html_string = re.sub(HtmlStatement.end_regex, '', selected_string, flags=re.IGNORECASE)
            html_string = re.sub(HtmlStatement.start_regex, '', html_string, flags=re.IGNORECASE)
            template.pasteHtml(html_string, cursor)

        # main of for_replace
        search = doc.createSearchDescriptor()
        search.SearchString = HtmlStatement.start_regex
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        x_found = doc.findFirst(search)
        while x_found is not None:
            compute_html(doc, x_found)
            x_found = doc.findNext(x_found.End, search)
