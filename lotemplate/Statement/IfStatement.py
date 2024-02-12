import re

from sorcery import dict_of
import lotemplate.errors as errors
from typing import Union
from com.sun.star.lang import XComponent

class IfStatement:
    """
    Class representing an if statement in a template libreoffice
    """
    start_regex = r"""
        \[\s*if\s*          # [if detection
          (?:
            (?:                 # parsing of var
              \$                # var start with $
              (\w+              # basic var name
                (\(             # parsing of fonction var
                  ((?:          # ?: is for non capturing group : the regex inside the parenthesis must be matched but does not create the capturing group
                    \\.|.       # everything that is escaped or every simple char
                  )*?)          # the ? before the ) in order to be not greedy (stop on the first unescaped ")"
                \))
              ?)                # the ? before the ) in order to be not greedy (won't go until the last ")")
            )
            |
            (?:                 # parsing of foritem
                \[\s*foritem\s*          # [foritem detection
                    (
                        \w+              # simple var of type abc
                        (?:\.\w+)*       # composite var name like abc.def
                    )
                    (?:\s+(escape_html|raw))?   # option pour escaper le contenu de la variable
                \s*\]
            )
            |
            (\[\s*forindex\s*\]) # parsing of forindex
          )
          \s*
          (                 # catch whether
              (?:           # for syntax == var or != var
                  (              # equality
                    \=\=|
                    \!\=|
                    \=\=\=|
                    \!\=\=|
                    CONTAINS|
                    NOT_CONTAINS
                  )\s*
                  (                 # value is anything, should escape [ and ]
                    (?:
                      \\.|.
                    )*
                  ?)                # not too greedy
              )
              |
              (IS_EMPTY|IS_NOT_EMPTY) # for syntax [if $toto IS_EMPTY] or [if $toto IS_NOT_EMPTY]
          )
        \s*\]
    """
    # remove comments, spaces and newlines
    start_regex = re.sub(r'#.*', '', start_regex).replace("\n", "").replace("\t", "").replace(" ", "")
    # print(start_regex)
    # \[\s*if\s*\$(\w+(\(((?:\\.|.)*?)\))?)\s*((?:(\=\=|\!\=)\s*((?:\\.|.)*?))|(IS_EMPTY|IS_NOT_EMPTY))\s*\]

    end_regex = r'\[\s*endif\s*\]'

    start_regex_light = r"""
        \[\s*if\s*                         # [if detection
          (?:(?:.*?)\[\s*for(?:.*?)\])?    # [foritem xxx] et [forindex] detection
          (?:.*?)                          # anything but not too greedy
        \]
    """
    # remove comments, spaces and newlines
    start_regex_light = re.sub(r'#.*', '', start_regex_light).replace("\n", "").replace("\t", "").replace(" ", "")

    def __init__(self, if_string):
        self.if_string = if_string
        match = re.search(self.start_regex, if_string, re.IGNORECASE)

        # for standard if outside for statements
        self.variable_name = match.group(1)
        # foritem parsing is used by if statements inside for statements if we want to check the value of a foritem value.
        self.foritem_name = match.group(4)
        self.foritem_escaping = match.group(5)
        # forindex parsing
        self.forindex = match.group(6)

        if match.group(8) is not None:
            # syntaxes like [if $foo == bar] or [if $foo != bar]
            self.operator = match.group(8)
            self.value = match.group(9)
        else:
            # syntaxes like [if $foo IS_EMPTY] or [if $foo IS_NOT_EMPTY]
            self.operator = match.group(10)

    def get_if_result(self, value):
        if self.operator == '==':
            return value.lower() == self.value.lower()
        if self.operator == '!=':
            return value.lower() != self.value.lower()
        if self.operator == '===':
            return value == self.value
        if self.operator == '!==':
            return value != self.value
        if self.operator == 'CONTAINS':
            return self.value.lower() in value.lower()
        if self.operator == 'NOT_CONTAINS':
            return self.value.lower() not in value.lower()
        if self.operator == 'IS_EMPTY':
            return re.search(r'^[\s\t\n]*$', value) is not None
        if self.operator == 'IS_NOT_EMPTY':
            return re.search(r'^[\s\t\n]*$', value) is None
        return False

    def scan_if(template) -> None:
        """
        scan for if statement. No return. We just verify that there is
        and endif for each if statement
        """
        def compute_if(x_found, x_found_endif):
            """
            Compute the if statement.
            """
            if_text = x_found.getText()
            endif_text = x_found_endif.getText()
            if_cursor = if_text.createTextCursorByRange(x_found)
            endif_cursor = endif_text.createTextCursorByRange(x_found_endif)
            content_cursor = if_text.createTextCursorByRange(x_found.End)
            content_cursor.gotoRange(x_found_endif.Start, True)

            match = re.search(IfStatement.start_regex, if_cursor.String, re.IGNORECASE)
            if match is None:
                raise errors.TemplateError(
                    'syntax_error_in_if_statement',
                    f"The statement {if_cursor.String} has a Syntax Error",
                    dict_of(if_cursor.String)
                )

            if_cursor.String = ''
            endif_cursor.String = ''
            content_cursor.String = ''

        def find_if_to_compute(doc, search, x_found):
            """
            Find the if statement to compute.
            """
            if x_found is None:
                return None
            while True:
                x_found_after = doc.findNext(x_found.End, search)
                if x_found_after is not None:
                    find_if_to_compute(doc, search, x_found_after)
                else:
                    break

            endif_search = doc.createSearchDescriptor()
            endif_search.SearchString = IfStatement.end_regex
            endif_search.SearchRegularExpression = True
            endif_search.SearchCaseSensitive = False

            x_found_endif = doc.findNext(x_found.End, endif_search)
            if x_found_endif is None:
                cursor = x_found.getText().createTextCursorByRange(x_found)
                raise errors.TemplateError(
                    'no_endif_found',
                    f"The statement {cursor.String} has no endif",
                    dict_of(cursor.String)
                )
            compute_if(x_found, x_found_endif)


        # main of if_replace
        doc = template.open_doc_from_url()
        search = doc.createSearchDescriptor()
        search.SearchString = IfStatement.start_regex_light
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        x_found = doc.findFirst(search)
        find_if_to_compute(doc, search, x_found)

        # check if there is still a endif at the end and rase an error if it is the case
        globalCursor = doc.getText().createTextCursor()
        globalCursor.gotoEnd(True)
        str = globalCursor.String
        match = re.search(IfStatement.end_regex, str, re.IGNORECASE)
        if match is not None:
            raise errors.TemplateError(
                'too_many_endif_found',
                f"The document has too many endif",
                {}
            )

        doc.dispose()


    def if_replace(doc: XComponent, local_variables: dict[str, dict[str, Union[str, list[str]]]]) -> None:
        """
        Parse statements like [if $myvar==TOTO]...[endif]

        If the condition matches we remove the if and endif statement.
        It the condition doesn't match, we remove the statements and the text between the statements.

        :param doc: the document to fill
        :param local_variables: the variables
        :return: None
        """

        def compute_if(x_found, x_found_endif):
            """
            Compute the if statement.
            """
            if_text = x_found.getText()
            endif_text = x_found_endif.getText()
            if_cursor = if_text.createTextCursorByRange(x_found)
            endif_cursor = endif_text.createTextCursorByRange(x_found_endif)
            content_cursor = if_text.createTextCursorByRange(x_found.End)
            content_cursor.gotoRange(x_found_endif.Start, True)
            if_statement = IfStatement(if_cursor.String)
            if_result = if_statement.get_if_result(local_variables[if_statement.variable_name]['value'])

            if not if_result:
                # if the if statement is not verified, we remove the paragraph with the if
                if_cursor.String = ''
                endif_cursor.String = ''
                content_cursor.String = ''
            elif if_result:
                # if the if statement is verified, we remove the if and endif statements
                if_cursor.String = ''
                endif_cursor.String = ''

        def find_if_to_compute(doc, search, x_found):
            """
            Find the if statement to compute.
            """
            if x_found is None:
                return None
            while True:
                x_found_after = doc.findNext(x_found.End, search)
                if x_found_after is not None:
                    find_if_to_compute(doc, search, x_found_after)
                else:
                    break

            endif_search = doc.createSearchDescriptor()
            endif_search.SearchString = IfStatement.end_regex
            endif_search.SearchRegularExpression = True
            endif_search.SearchCaseSensitive = False

            x_found_endif = doc.findNext(x_found.End, endif_search)
            if x_found_endif is None:
                cursor = x_found.getText().createTextCursorByRange(x_found)
                raise errors.TemplateError(
                    'no_endif_found',
                    f"The statement {cursor.String} has no endif",
                    dict_of(cursor.String)
                )
            compute_if(x_found, x_found_endif)


        # main of if_replace
        search = doc.createSearchDescriptor()
        search.SearchString = IfStatement.start_regex
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        x_found = doc.findFirst(search)
        find_if_to_compute(doc, search, x_found)
