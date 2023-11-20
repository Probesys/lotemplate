import re
from com.sun.star.lang import XComponent

class CounterStatement:
    counter_regex = r"""
        \[\s*
            (?:
                (?:
                    (counter)
                    (?:\s+(\w+))
                    (?:\s+(hidden))?
                )
                |
                (?:
                    (counter\.reset|counter\.last)
                    (?:\s+(\w+))
                )
                |
                (?:
                    (counter\.format)
                    (?:\s+(\w+))
                    (?:\s+(number|letter_uppercase|letter_lowercase))            
                )
            )
        \s*\]
    """
    counter_regex = re.sub(r'#.*', '', counter_regex).replace("\n", "").replace("\t", "").replace(" ", "")

    def __init__(self, counter_string: str):
        self.counter_string = counter_string
        match = re.search(self.counter_regex, counter_string, re.IGNORECASE)

        if match.group(1) is not None:
            self.command_name = match.group(1)
            self.counter_name = match.group(2)
            self.is_hidden = match.group(3) is not None
        elif match.group(4) is not None:
            self.command_name = match.group(4)
            self.counter_name = match.group(5)
        elif match.group(6) is not None:
            self.command_name = match.group(6)
            self.counter_name = match.group(7)
            self.counter_format = match.group(8)

class CounterManager:
    """
    Class representing an html statement in a template libreoffice
    """

    def __init__(self, html: str, component: XComponent):
        self.counter_list = {}

    def scan_counter(doc: XComponent) -> None:
        """
        scan for counter statement. No return. We just verify that there is
        and endif for each if statement
        """
        def compute_counter(x_found):
            """
            Compute the counter statement.
            """
            counter_text = x_found.getText()
            counter_cursor = counter_text.createTextCursorByRange(x_found)
            cursor_statement = CounterStatement(counter_cursor.String)

        def find_counter_to_compute(doc, search, x_found):
            """
            Find the if statement to compute.
            """
            if x_found is None:
                return None

            compute_counter(x_found)

            # searching for the next counter statement.
            x_found_after = doc.findNext(x_found.End, search)
            if x_found_after is not None:
                find_counter_to_compute(doc, search, x_found_after)

        # main of if_replace
        search = doc.createSearchDescriptor()
        search.SearchString = CounterStatement.counter_regex
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        x_found = doc.findFirst(search)
        find_counter_to_compute(doc, search, x_found)

    def counter_replace(doc: XComponent) -> None:
        """
        scan for counter statement. No return. We just verify that there is
        and endif for each if statement
        """
        def compute_counter(x_found):
            """
            Compute the counter statement.
            """
            def number_formated(format: str, value: int) -> str:
                if format=='number':
                    return str(value)
                elif format=='letter_uppercase':
                    # after Z we go to A
                    value -= 1
                    value = value % 26
                    return chr(value + 65)
                elif format=='letter_lowercase':
                    # after z we go to a
                    value -= 1
                    value = value % 26
                    return chr(value + 97)
                return str(value)

            counter_text = x_found.getText()
            counter_cursor = counter_text.createTextCursorByRange(x_found)
            counter_statement = CounterStatement(counter_cursor.String)
            if counter_statement.counter_name not in counter_list:
                counter_list[counter_statement.counter_name] = {
                    "value": 0,
                    "format": "number"
                }
            if counter_statement.command_name == 'counter':
                counter_list[counter_statement.counter_name]["value"] = counter_list[counter_statement.counter_name]["value"] + 1
                if not counter_statement.is_hidden:
                    counter_cursor.String = number_formated(counter_list[counter_statement.counter_name]["format"], counter_list[counter_statement.counter_name]["value"])
                else:
                    counter_cursor.String = ""
            elif counter_statement.command_name == 'counter.format':
                counter_list[counter_statement.counter_name]["format"] = counter_statement.counter_format
                counter_cursor.String = ""
            elif counter_statement.command_name == 'counter.reset':
                counter_list[counter_statement.counter_name]["value"] = 0
                counter_cursor.String = ""
            elif counter_statement.command_name == 'counter.last':
                counter_cursor.String = number_formated(counter_list[counter_statement.counter_name]["format"], counter_list[counter_statement.counter_name]["value"])

        def find_counter_to_compute(doc, search, x_found):
            """
            Find the if statement to compute.
            """
            if x_found is None:
                return None

            text = x_found.getText()
            cursor = text.createTextCursorByRange(x_found)
            str = cursor.String


            compute_counter(x_found)

            # searching for the next counter statement.
            x_found_after = doc.findNext(x_found.End, search)
            if x_found_after is not None:
                find_counter_to_compute(doc, search, x_found_after)

        # main of counter_replace
        counter_list = {}
        search = doc.createSearchDescriptor()
        search.SearchString = CounterStatement.counter_regex
        search.SearchRegularExpression = True
        search.SearchCaseSensitive = False
        x_found = doc.findFirst(search)
        find_counter_to_compute(doc, search, x_found)
