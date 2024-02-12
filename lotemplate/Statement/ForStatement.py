import re
from sorcery import dict_of
import lotemplate.errors as errors
from typing import Union
from com.sun.star.lang import XComponent
from lotemplate.Statement.IfStatement import IfStatement

class ForStatement:
    """
    Class representing an for statement in a template libreoffice
    """
    start_regex = r"""
        \[\s*for\s+          # [if detection
          \$                # var start with $
          (\w+              # basic var name
            (\(             # parsing of fonction var
              ((?:          # ?: is for non capturing group : the regex inside the parenthesis must be matched but does not create the capturing group
                \\.|.       # everything that is escaped or every simple char
              )*?)          # the ? before the ) in order to be not greedy (stop on the first unescaped ")"
            \))
          ?)                # the ? before the ) in order to be not greedy (won't go until the last ")")
        \s*\]
    """
    # remove comments, spaces and newlines
    start_regex = re.sub(r'#.*', '', start_regex).replace("\n", "").replace("\t", "").replace(" ", "")
    # print(start_regex)
    # \[\s*for\s*\$(\w+(\(((?:\\.|.)*?)\))?)\s*\]

    start_regex_light = r"""
        \[\s*for\s          # [for detection
          (?:.*?)            # anything before the var name
        \]
    """
    # remove comments, spaces and newlines
    start_regex_light = re.sub(r'#.*', '', start_regex_light).replace("\n", "").replace("\t", "").replace(" ", "")

    foritem_regex = r"""
        \[\s*foritem\s*          # [foritem detection
            (
                \w+              # simple var of type abc
                (?:\.\w+)*       # composite var name like abc.def
            )
            (?:\s+(escape_html|raw))?   # option pour escaper le contenu de la variable
        \s*\]
    """
    foritem_regex = re.sub(r'#.*', '', foritem_regex).replace("\n", "").replace("\t", "").replace(" ", "")
    # print(foritem_regex)
    # \[\s*foritem\s*((\w+)(?:\.\w+)*)\s*\]

    # [forindex] is replaced by the counter of the loop. A string starting at 0
    forindex_regex = r'\[\s*forindex\s*\]'

    end_regex = r'\[\s*endfor\s*\]'

    def __init__(self, for_string):
        self.for_string = for_string
        match = re.search(self.start_regex, for_string, re.IGNORECASE)
        if match is None:
            raise errors.TemplateError(
                'syntax_error_in_for_statement',
                f"Syntax Error in for statement : {for_string}",
                dict_of(for_string)
            )
        self.variable_name = match.group(1)

    def scan_for(doc: XComponent) -> dict:
        """
        scan for statement. return list of vars.

        We verify that
        - there is and endfor for each for statement
        - vars sent are lists
        """

        def scan_single_for(doc: XComponent, local_x_found) -> str:
            """
            scan for a single for statement
            """
            for_statement = ForStatement(local_x_found.getString())
            position_in_text = len(for_statement.for_string)

            endfor_search = doc.createSearchDescriptor()
            endfor_search.SearchString = ForStatement.end_regex
            endfor_search.SearchRegularExpression = True
            endfor_search.SearchCaseSensitive = False
            x_found_endfor = doc.findNext(local_x_found.End, endfor_search)
            if x_found_endfor is None:
                raise errors.TemplateError(
                    'no_endfor_found',
                    f"The statement {for_statement.for_string} has no endfor",
                    dict_of(for_statement.for_string)
                )
            return for_statement.variable_name

        search = doc.createSearchDescriptor()
        search.SearchString = ForStatement.start_regex_light
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        x_found = doc.findFirst(search)

        for_vars = {}
        while x_found is not None:
            variable_name = scan_single_for(doc, x_found)
            for_vars[variable_name] = {'type': 'array', 'value': []}
            x_found = doc.findNext(x_found.End, search)
        return for_vars


    def for_replace(doc: XComponent, local_variables: dict[str, dict[str, Union[str, list[str]]]]) -> None:
        """
        Parse statements like [for $myvar]...[endfor]

        We replace the for and endfor statements with the text between them, for each value in the variable.

        :param doc: the document to fill
        :param local_variables: the variables
        :return: None
        """

        def compute_for(doc, local_x_found):
            """
            for one single for statement, cut and paste the content of the for
            :param local_x_found:
            :return:
            """

            def escape_html(s):
                """
                Replace special characters "&", "<" and ">" to HTML-safe sequences.
                If the optional flag quote is true, the quotation mark character (")
                is also translated.
                """
                s = s.replace("&", "&amp;")  # Must be done first!
                s = s.replace("<", "&lt;")
                s = s.replace(">", "&gt;")
                s = s.replace('"', "&quot;")
                return s

            def getForitemValue(match_var_name, match_escaping, foritem_var):
                """
                we are in a for loop on values of an array.

                a regex just detected [foritem match_var_name match_escaping]

                mathch escaping, can exist or not. If it exists, it can be raw or escape_html

                :param match_var_name:
                :param match_escaping:
                :return:
                """
                # get separate the var_name by "." to get the value in the dict
                var_name_hierarchy = match_var_name.split('.')
                # get the variable value from the hierarchy
                value = foritem_var
                for var_name in var_name_hierarchy:
                    value = value[var_name]

                # get the escaping
                escaping = 'raw'
                if match_escaping is not None:
                    escaping = match_escaping
                # escape the value
                if escaping == 'escape_html':
                    value = escape_html(value)
                return str(value)

            def manage_if_inside_for(content, local_variables, foritem_var, forindex):
                """
                manage the if statements inside a for loop.

                It uses a recursive approach : we search an if statement inside the content string. Then we create a
                subcontent with the content after the if statement and call the function again on this substring.

                With this recursive call, the process begins with the last if statement and update the content for
                the previous call.

                :param content:
                :param local_variables:
                :param foritem_var:
                :return:
                """
                # look for the first if statement
                match_if = re.search(IfStatement.start_regex, content, re.IGNORECASE)
                if match_if is None:
                    return content

                # get content before the if statement and call recursively the function
                subcontent = content[match_if.end():]
                subcontent = manage_if_inside_for(subcontent, local_variables, foritem_var, forindex)

                # update the content with the result of the recursive call
                content = content[:match_if.end()] + subcontent

                # get the if statement values
                if_statement = IfStatement(match_if.group(0))

                # precontent is the content before the if statement
                precontent = content[:match_if.start()]
                postcontent = content[match_if.start():]
                match_if_postcontent = re.search(IfStatement.start_regex, postcontent, re.IGNORECASE)

                # if no endif => throw error
                match_endif_postcontent = re.search(IfStatement.end_regex, postcontent, re.IGNORECASE)
                if match_endif_postcontent is None:
                    raise errors.TemplateError(
                        'no_endif_found',
                        f"The statement {if_statement.if_string} has no endif",
                        dict_of(if_statement.if_string)
                    )

                # get value associated to the if statement
                value = None
                if if_statement.variable_name is not None:
                    computed_variable_name = re.sub(ForStatement.forindex_regex, forindex, if_statement.variable_name)
                    value = local_variables[computed_variable_name]['value']
                if if_statement.foritem_name is not None:
                    value = getForitemValue(if_statement.foritem_name, if_statement.foritem_escaping, foritem_var)
                if if_statement.forindex is not None:
                    value = forindex
                if_result = if_statement.get_if_result(value)

                if if_result:
                    postcontent = postcontent[:match_endif_postcontent.start()] + postcontent[match_endif_postcontent.end():]
                    postcontent = postcontent[:match_if_postcontent.start()] + postcontent[match_if_postcontent.end():]
                if not if_result:
                    postcontent = postcontent[:match_if_postcontent.start()] + postcontent[match_endif_postcontent.end():]

                return precontent + postcontent


            for_statement = ForStatement(local_x_found.getString())
            foritem_vars = local_variables[for_statement.variable_name]['value']

            # select content between for and endfor (including endfor)
            endfor_search = doc.createSearchDescriptor()
            endfor_search.SearchString = ForStatement.end_regex
            endfor_search.SearchRegularExpression = True
            endfor_search.SearchCaseSensitive = False
            x_found_endfor = doc.findNext(local_x_found.End, endfor_search)
            if x_found_endfor is None:
                raise errors.TemplateError(
                    'no_endfor_found',
                    f"The statement {for_statement.for_string} has no endfor",
                    dict_of(for_statement.for_string)
                )

            for_text = local_x_found.getText()
            endfor_text = x_found_endfor.getText()
            for_cursor = for_text.createTextCursorByRange(local_x_found)
            endfor_cursor = endfor_text.createTextCursorByRange(x_found_endfor)
            content_cursor = for_text.createTextCursorByRange(local_x_found.End)
            content_cursor.gotoRange(x_found_endfor.Start, True)

            # remove the for statement from the odt
            for_cursor.String = ''

            # get the content between the for and the endfor
            template = content_cursor.String

            # remove the content from the file
            content_cursor.String = ''

            # remove the endfor at the end
            endfor_cursor.String = ''

            # loop on values of the variable
            counter = 0
            for foritem_var in foritem_vars:
                content = template
                # parse if inside for before managing foritem replacements
                content = manage_if_inside_for(content, local_variables, foritem_var, str(counter))

                # search [forindex] and remplace by my counter
                content = re.sub(ForStatement.forindex_regex, str(counter), content, flags=re.IGNORECASE)

                # replace inside the selected content selected
                for match in re.finditer(ForStatement.foritem_regex, content, re.IGNORECASE):
                    getForitemValue(match.group(1), match.group(2), foritem_var)
                    # replace the variable by its value
                    content = content.replace(
                        match.group(0),
                        getForitemValue(match.group(1), match.group(2), foritem_var)
                    )

                # paste the content
                for_text.insertString(for_cursor, content, False)

                # counter increment
                counter += 1

        # main of for_replace
        search = doc.createSearchDescriptor()
        search.SearchString = ForStatement.start_regex
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        x_found = doc.findFirst(search)
        while x_found is not None:
            compute_for(doc, x_found)
            x_found = doc.findNext(x_found.End, search)

