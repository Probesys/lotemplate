from com.sun.star.lang import XComponent
from typing import Union
from lotemplate.Statement.CalcSearchStatement import  CalcTextStatement
from com.sun.star.sheet.CellInsertMode import  DOWN, RIGHT
from com.sun.star.sheet.CellDeleteMode import   UP, LEFT 
import re


def incr_chr(c):
    return chr(ord(c) + 1) if c != 'Z' else 'A'

def incr_str(s,numb):
    for  i in range(numb):
        lpart = s.rstrip('Z')
        num_replacements = len(s) - len(lpart)
        new_s = lpart[:-1] + incr_chr(lpart[-1]) if lpart else 'A'
        new_s += 'A' * num_replacements
        s=new_s
    return new_s


class CalcTableStatement:
    table_pattern = re.compile("^loop_(down|right)_(.+)",re.IGNORECASE)

    def isTableVar(var):
        if re.match(CalcTableStatement.table_pattern,var):
            return True
        else:
            return False

    def scan(doc: XComponent, get_list=False) -> Union[dict, list]:
        """
        scan for tables in the given doc

        :param get_list: indicates if the function should return a list
        of variables or the formatted dictionary of variables
        :param doc: the document to scan
        :return: the scanned variables
        """

        def scan_range(myrange) -> None:
            """
            scan for variables in the given cell

            :param cell: the cell to scan
            :return: None
            """
            nonlocal doc
            return CalcTextStatement.scan(myrange,True)
        tab_vars = {}
        for  NamedRange in doc.NamedRanges:
            if re.match(CalcTableStatement.table_pattern,NamedRange.getName()):
                named = scan_range(NamedRange)
                tab_vars[NamedRange.getName()] = {'type': 'object', 'value': named}

        return tab_vars

    def fill(doc: XComponent, variable: str, value) -> None:
        """
        Fills all the table-related content

        :param doc: the document to fill
        :param variable: the variable to search
        :param value: the value to replace with
        :return: None
        """
        myrange=doc.NamedRanges.getByName(variable)
        #mycellrange=myrange.getReferredCells()
        mycellrangeaddr=myrange.getReferredCells().getRangeAddress()


        mycontent,finalcol,finalrow =myrange.getContent().rsplit('$', 2)

        StartColumn=myrange.getReferredCells().getRangeAddress().StartColumn
        StartRow=myrange.getReferredCells().getRangeAddress().StartRow
        EndColumn=myrange.getReferredCells().getRangeAddress().EndColumn
        EndRow=myrange.getReferredCells().getRangeAddress().EndRow
        maxlen=max([len(value[x]['value']) for x in value])
        sheet=doc.getSheets()[mycellrangeaddr.Sheet]

        match = re.match(CalcTableStatement.table_pattern, variable)
        direction = match.group(1)
        if direction=="right":
            size=1+EndColumn-StartColumn
            left=True
            decale=RIGHT
            delete=LEFT
        elif direction=="down":
            size=1+EndRow-StartRow
            left=False
            decale=DOWN
            delete=UP

        for i in reversed(range(maxlen)):
            sheet.insertCells(mycellrangeaddr,decale)
            copycell=sheet.getCellByPosition(StartColumn,StartRow)
            rangetocopy=sheet.getCellRangeByPosition(StartColumn,StartRow,EndColumn,EndRow )
            sheet.copyRange(copycell.CellAddress,doc.NamedRanges.getByName(variable).getReferredCells().getRangeAddress())
            for key, mylist  in sorted(value.items(), key=lambda x: len(x[0]), reverse=True):
                try:
                    CalcTextStatement.fill(rangetocopy,'&'+key,mylist['value'][i])
                except IndexError:
                    CalcTextStatement.fill(rangetocopy,'&'+key,"") 

        if left:
           myrange.setContent(mycontent+'$'+incr_str(finalcol,maxlen*size)+'$'+finalrow)
           mycellrangeaddr.EndColumn=mycellrangeaddr.EndColumn+maxlen*size
           mycellrangeaddr.StartColumn=mycellrangeaddr.StartColumn+maxlen*size

        else:
           myrange.setContent(mycontent+'$'+finalcol+'$'+str(int(finalrow)+(maxlen-1)*size))
           mycellrangeaddr.EndRow=mycellrangeaddr.EndRow+maxlen*size
           mycellrangeaddr.StartRow=mycellrangeaddr.StartRow+maxlen*size

        sheet.removeRange(mycellrangeaddr,delete)
