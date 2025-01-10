"""
Copyright (C) 2023 Probesys


The classes used for document connexion and manipulation
"""

__all__ = (
    'CalcTemplate',
)
from typing import Union



from . import errors

from lotemplate.Statement.CalcTableStatement import CalcTableStatement
from .Template import Template
from lotemplate.Statement.CalcSearchStatement import CalcTextStatement
from jsondiff import diff

class CalcTemplate(Template):
    formats = {
            "ods": "calc8",
            "pdf": "calc_pdf_Export",
            "html": "HTML (StarCalc)",
            "csv": "Text - txt - csv (StarCalc)",
            'xls': 'MS Excel 2003 XML',
            'xlsx': 'Calc MS Excel 2007 XML'
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

        if not doc or not doc.supportsService('com.sun.star.sheet.SpreadsheetDocument'):
            self.close()
            raise errors.TemplateError(
                'invalid_format',
                f"The given format ({self.file_name.split('.')[-1]!r}) is invalid, or the file is already open by "
                f"an other process (accepted formats: ODS, OTS, XLS, XLSX, CSV)",
                dict(format=self.file_name.split('.')[-1])
            )
        return doc




    def scan(self, **kwargs) -> dict[str: dict[str, Union[str, list[str]]]]:
        """
        scans the variables contained in the template. Supports text, tables and images

        :return: list containing all the variables founded in the template
        """

        #should_close = kwargs.get("should_close", False)
        texts = {} 
        #(Pdb) self.doc.getSheets().getElementNames()
        for sheet in self.doc.getSheets():
            texts = texts | CalcTextStatement.scan(sheet)
        tables=CalcTableStatement.scan(self.doc)
        #texts = CalcTextStatement.scan_Document_text(self.doc)
        #pdb.set_trace()
        return texts | tables 


    def search_error(self, json_vars: dict[str, dict[str, Union[str, list[str]]]]) -> None:
        """
        find out which variable is a problem, and raise the required error

        :param json_vars: the given json variables
        :return: None
        """
        notdiff=diff(json_vars, self.variables)
        if  not notdiff:
            return
        else:
           raise errors.JsonComparaisonError(
                'missing_required_variable',
                f"The json are not the same here is the diff "
                f"{notdiff}",
                dict(variable=notdiff)
            )

        # when parsing the template, we assume that all vars are of type text. But it can also be of type html.
        # So we check if types are equals or if type in json is "html" while type in template is "text"
        json_incorrect = [key for key in self.variables if (json_vars[key]['type'] != self.variables[key]['type']) and (json_vars[key]['type'] != "html" or self.variables[key]['type']!="text")]
        if json_incorrect:
            raise errors.JsonComparaisonError(
                'incorrect_value_type',
                f"The variable {json_incorrect[0]!r} should be of type "
                f"{self.variables[json_incorrect[0]]['type']!r}, like in the template, but is of type "
                f"{json_vars[json_incorrect[0]]['type']!r}",
                dict(variable=json_incorrect[0], actual_variable_type=json_vars[json_incorrect[0]]['type'],
                     expected_variable_type=self.variables[json_incorrect[0]]['type'])
            )

        template_missing = [key for key in set(json_vars) - set(self.variables)]
        json_vars_without_template_missing = {key: json_vars[key] for key in json_vars if key not in template_missing}
        if json_vars_without_template_missing == self.variables:
            return


    def fill(self, variables: dict[str, dict[str, Union[str, list[str]]]]) -> None:
        """
        Fills a template copy with the given values

        :param variables: the values to fill in the template
        :return: None
        """

        ###
        ### main calls
        ###
        objects={}
        for var, details in sorted(variables.items(), key=lambda s: -len(s[0])):
            if details['type'] == 'text':
                for sheet in self.doc.getSheets():
                    CalcTextStatement.fill(sheet, "$" + var, details['value'])
            elif details['type'] == "object" and  CalcTableStatement.isTableVar(var) :
                    objects[var]=details
        for  var, details in objects.items():
            CalcTableStatement.fill(self.doc, var, details['value'])

