from com.sun.star.lang import XComponent
from com.sun.star.sheet import XCellRangeData
from typing import Union
import lotemplate.errors as errors
import regex


class TableStatement:
    table_regex = regex.compile(
        r'\$\w+'
        r'(?:\((?<arg>(?R)|"[^"]*"|[^$&"\s()][^\s()]*)(?:[+ ](?&arg))*\))?'
        r'|(?<var>&\w+)'
    )

    def scan_table(doc: XComponent, get_list=False) -> Union[dict, list]:
        """
        scan for tables in the given doc

        :param get_list: indicates if the function should return a list
        of variables or the formatted dictionary of variables
        :param doc: the document to scan
        :return: the scanned variables
        """

        def scan_cell(cell) -> None:
            """
            scan for variables in the given cell

            :param cell: the cell to scan
            :return: None
            """
            for match in TableStatement.table_regex.finditer(cell):
                if not match.captures('var'):
                    continue
                if row_i != nb_rows - 1:
                    raise errors.TemplateError(
                        'variable_not_in_last_row',
                        f"The variable {match[0]!r} (table {t_name!r}) "
                        f"isn't in the last row (got: row {row_i + 1!r}, "
                        f"expected: row {nb_rows!r})",
                        dict(table=t_name, actual_row=row_i + 1,
                             expected_row=nb_rows, variable=match[0])
                    )
                tab_vars[match[0][1:]] = {'type': 'table', 'value': ['']}
                list_tab_vars.append(match[0])

        tab_vars = {}
        list_tab_vars = []
        for i in range(doc.getTextTables().getCount()):
            table = doc.getTextTables().getByIndex(i)
            if not isinstance(table, XCellRangeData):
                continue
            table_data = table.getDataArray()
            t_name = doc.getTextTables().getByIndex(i).getName()
            nb_rows = len(table_data)
            for row_i, row in enumerate(table_data):
                for column in row:
                    scan_cell(column)

        return list_tab_vars if get_list else tab_vars

    def tables_fill(doc: XComponent, variables: dict[str, dict[str, Union[str, list[str]]]], text_prefix: str,
                    table_prefix: str) -> None:
        """
        Fills all the table-related content

        :param doc: the document to fill
        :param text_prefix: the prefix for text variables
        :param table_prefix: the prefix for table variables
        :return: None
        """
        search = doc.createSearchDescriptor()
        matches = []
        for element, infos in sorted(variables.items(), key=lambda s: -len(s[0])):
            if infos['type'] != 'table':
                continue
            search.SearchString = (text_prefix if '(' in element else table_prefix) + element
            founded = doc.findAll(search)
            matches += [founded.getByIndex(i) for i in range(founded.getCount()) if founded.getByIndex(i).TextTable]
        tab_vars = [{
            "table": variable.TextTable,
            "var": variable.String
        } for variable in matches]

        tables = [
            {'table': tab, 'vars':
                {tab_var['var']: variables[tab_var['var'][1:]]['value']
                 for tab_var in tab_vars if tab_var['table'] == tab}
             } for tab in list(set(variable['table'] for variable in tab_vars))
        ]

        for element in tables:

            table = element['table']
            table_vars = element['vars']
            var_row_pos = len(table.getRows()) - 1
            nb_rows_to_add = max([len(variable) for variable in table_vars.values()])
            table.getRows().insertByIndex(var_row_pos + 1, nb_rows_to_add - 1)
            table_values = table.getDataArray()
            var_row = table_values[var_row_pos]
            static_rows = table_values[:var_row_pos]

            for i in range(nb_rows_to_add):
                new_row = var_row
                for variable_name, variable_value in sorted(table_vars.items(), key=lambda s: -len(s[0])):
                    new_row = tuple(
                        elem.replace(
                            variable_name, variable_value[i]
                            if i < len(variable_value) else ""
                        ) for elem in new_row
                    )
                static_rows += (new_row,)
            table.setDataArray(static_rows)
