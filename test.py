# encoding=UTF-8

import os, fcntl,sys
import unohelper
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Size
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK, LINE_BREAK
from com.sun.star.awt.FontWeight import BOLD as FW_BOLD
from com.sun.star.table import CellRangeAddress
from com.sun.star.table import XTableRows
import uno
import configargparse
import argparse
import json


flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
fcntl.fcntl(
    sys.stdin.fileno(),
    fcntl.F_SETFL,
    flags | os.O_NONBLOCK
)
class oo_template(object):
    def convert(self,oo_connect,file,datas,out_file):
        self.desktop = oo_connect[0]
        self.graphicprovider = oo_connect[1]
        url = unohelper.systemPathToFileUrl(os.path.dirname(os.path.abspath(__file__))+"/"+file)
        self.dpi = 150
        self.edit_doc = self.desktop.loadComponentFromURL(url, "_blank", 0, ())
        self.cursor = self.edit_doc.Text.createTextCursor()
        self.cursor.gotoEnd(False)
        self.cl_ID = 0
        # do what ever you like from the following function
        oWriterTables = self.edit_doc.getTextTables()
        print(datas)
        for (key, data) in datas.items():
            if isinstance(data, str):
                self.do_search_and_replace("$"+key,data)
            elif isinstance(data, list):
                self.convert_table(oWriterTables.getByName("$"+key),data)

        #self.add_embedded_image(os.path.dirname(os.path.abspath(__file__))+'/test.jpg')
        fileurl = unohelper.systemPathToFileUrl(os.path.dirname(os.path.abspath(__file__))+'/test.jpg')
        graphic = self.graphicprovider.queryGraphic((PropertyValue('URL', 0, fileurl, 0), ))
        #old=self.edit_doc.getGraphicObjects().getByName('$photo')       
        self.edit_doc.getGraphicObjects().getByName('$photo').Graphic=graphic
            #graphic_object_shape = doc.createInstance('com.sun.star.drawing.GraphicObjectShape')
            #graphic_object_shape.Graphic = graphic
        #self.edit_doc.getGraphicObjects().getByName('$photo')
        url2 = unohelper.systemPathToFileUrl(os.path.dirname(os.path.abspath(__file__))+'/test1.odt')
        self.edit_doc.storeAsURL(url2,())


        property = (
            PropertyValue( "FilterName" , 0, "writer_pdf_Export" , 0 ),
        )
        url3 = unohelper.systemPathToFileUrl(os.path.dirname(os.path.abspath(__file__))+'/test1.pdf')
        self.edit_doc.storeToURL(url3,property)
        self.edit_doc.dispose()
    # search and replace text
    def convert_table(self,table,data):
        print(table.getRows().getCount())
        rows=table.getRows()
        rows.insertByIndex(2, len(data)-1)
        #table.getByIndex(2)
                   # Source address

        # Restore cell address variable
        #self._oCellAddress = self._oRange.getReferencePosition()
        table_data=table.getDataArray()
        template= table_data[1]
        myarray=(table_data[0],)
        for (mydata ) in data:
            tmp=template
            for (k,d) in mydata.items():
                tmp = tuple(map(lambda x: x.replace('$'+k,d), tmp))
            myarray=myarray+(tmp,)
        #table.setDataArray((('aaa', 'bbbb'), ('Ccc', 'ddd'), ('zzzz', 'zzzzz'),('zzzz', 'zzzzz')))
        table.setDataArray(myarray)
    def do_search_and_replace(self, searchtext=None, replacetext=None):
        doc = self.edit_doc
        if searchtext is None or replacetext is None:
            return

        search = doc.createSearchDescriptor()
        search.SearchString = searchtext
        found = doc.findFirst(search)

        while found:
            found.String = found.String.replace(searchtext, replacetext)
            found = doc.findNext(found.End, search)

    def add_embedded_image(self, url=None, width=None, height=None, paraadjust=None):
        dpi = self.dpi
        scale = 1000 * 2.54 / float(dpi)
        doc = self.edit_doc
        cursor = doc.Text.createTextCursor()
        cursor.gotoEnd(False)
        try:
            fileurl = unohelper.systemPathToFileUrl(url)
            graphic = self.graphicprovider.queryGraphic((PropertyValue('URL', 0, fileurl, 0), ))
            if graphic.SizePixel is None:
                # Then we're likely dealing with vector graphics. Then we try to
                # get the "real" size, which is enough information to
                # determine the aspect ratio
                original_size = graphic.Size100thMM
            else:
                original_size = graphic.SizePixel
            graphic_object_shape = doc.createInstance('com.sun.star.drawing.GraphicObjectShape')
            graphic_object_shape.Graphic = graphic
            if width and height:
                size = Size(int(width * scale), int(height * scale))
            elif width:
                size = Size(int(width * scale), int((float(width)/original_size.Width) * original_size.Height * scale))
            elif height:
                size = Size(int((float(height)/original_size.Height) * original_size.Width * scale), int(height * scale))
            else:
                size = Size(int(original_size.Width * scale), original_size.Height * scale)
            graphic_object_shape.setSize(size)
            # doc.Text.insertTextContent(cursor, graphic_object_shape, False)
            thisgraphicobject = doc.createInstance("com.sun.star.text.TextGraphicObject")
            thisgraphicobject.Graphic = graphic_object_shape.Graphic
            thisgraphicobject.setSize(size)
            if paraadjust:
                oldparaadjust = cursor.ParaAdjust
                cursor.ParaAdjust = paraadjust
            doc.Text.insertTextContent(cursor, thisgraphicobject, False)
            #os.unlink(url)
            if paraadjust:
                cursor.ParaAdjust = oldparaadjust
        except Exception as e:
            print(e)




def connect(host="localhost",port="2002"):
        # Connect to LibreOffice.config['bitbucket.org']['User']
        localContext = uno.getComponentContext()
        servicemanager = localContext.ServiceManager
        resolver = servicemanager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
        context = resolver.resolve("uno:socket,host=%s,port=%s;urp;StarOffice.ComponentContext" % (host,port))
        desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)
        # generate a graphic provider as well to embed images from filesystem
        graphicprovider = context.ServiceManager.createInstance('com.sun.star.graphic.GraphicProvider')
        return desktop, graphicprovider


if __name__ == '__main__':
    p = configargparse.ArgParser(default_config_files=['config.ini'])
    p.add('-c', '--config', is_config_file=True, help='config file path')
    p.add('--host', required=True, help='host connection libreoffice')  # this option can be set in a config file because it starts with '--'
    p.add('--port', help='port')
    p.add('input',nargs='?',default=sys.stdin)
    p.add('-d',"--data",help='file with data in json put')
    p.add('-f','--file', default='test.odt', help='oo template')
    p.add('-t','--to_file', default='test1.odt', help='out file')
    options = p.parse_args()


    print(options)
    if options.data is not None :
        io_f= open(options.data)
    else:
        io_f=options.input
    datas=json.loads(io_f.read())
    oo_connect =connect(options.host, options.port)
    oo_template = oo_template()
    oo_template.convert(oo_connect,options.file,datas,options.to_file)
