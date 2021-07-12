"""
depreciated - use this as a code exemple only
"""
# encoding=UTF-8

import os
import fcntl
import sys
import unohelper
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Size
import uno
import configargparse
import json
from PIL import Image
from PIL import ImageOps


# empêche le blocage de l'input, le lit directement sans s'y arrêter
flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
fcntl.fcntl(
    sys.stdin.fileno(),
    fcntl.F_SETFL,
    flags | os.O_NONBLOCK
)


class oo_template(object):

    def list_vars(self, oo_connect, file):
        self.desktop = oo_connect[0]
        self.graphicprovider = oo_connect[1]
        url = unohelper.systemPathToFileUrl(os.path.dirname(
            os.path.abspath(__file__)) + "/" + file)
        self.dpi = 150
        self.edit_doc = self.desktop.loadComponentFromURL(url, "_blank", 0, ())
        self.cursor = self.edit_doc.Text.createTextCursor()
        self.oWriterTables = self.edit_doc.getTextTables()
        self.cursor.gotoEnd(False)
        self.cl_ID = 0
        doc = self.edit_doc
        search = doc.createSearchDescriptor()
        search.SearchRegularExpression = True
        search.SearchString = '\\$[:alnum:]*'
        found = doc.findFirst(search)
        vars = {}
        while found:
            print(found.String)
            if found.TextTable is not None:  # censé gérer les cas quand une variable est dans un tableau,
                # mais ne vérifie absolument pas si le tableau est une variable ;
                # en bref, une tentative échouée de trouver un concept pour remplir dynamiquement les tableaux
                if found.TextTable.Name[1:] in vars:
                    vars[found.TextTable.Name[1:]][0][found.String[1:]] = ""
                else:
                    vars[found.TextTable.Name[1:]] = [{found.String[1:]: ""}]
            else:
                vars[found.String[1:]] = ""
            found = doc.findNext(found.End, search)
        print(self.edit_doc.getGraphicObjects().getElementNames())
        # while found:
        #    print(found)
        print(json.dumps(vars))

    def convert(self, oo_connect, file, datas, out_file):
        self.desktop = oo_connect[0]
        self.graphicprovider = oo_connect[1]
        url = unohelper.systemPathToFileUrl(os.path.dirname(
            os.path.abspath(__file__)) + "/" + file)
        self.dpi = 150
        self.edit_doc = self.desktop.loadComponentFromURL(url, "_blank", 0, ())
        self.cursor = self.edit_doc.Text.createTextCursor()
        self.oWriterTables = self.edit_doc.getTextTables()
        self.cursor.gotoEnd(False)
        self.cl_ID = 0
        # do what ever you like from the following function
        print(datas)
        for (key, data) in datas.items():
            if isinstance(data, str):
                self.do_search_and_replace("$" + key, data)
            elif isinstance(data, list):
                self.convert_table(key, data)
            elif isinstance(data, object):
                self.convert_image(key, data)

        url2 = unohelper.systemPathToFileUrl(
            os.path.dirname(os.path.abspath(__file__)) + '/test_files/output/test1.odt')
        self.edit_doc.storeAsURL(url2, ())

        property = (
            PropertyValue("FilterName", 0, "writer_pdf_Export", 0),
        )
        url3 = unohelper.systemPathToFileUrl(os.path.dirname(
            os.path.abspath(__file__)) + '/test_files/output/est1.pdf')
        self.edit_doc.storeToURL(url3, property)
        self.edit_doc.dispose()
    # search and replace text

    def convert_image(self, name, data):
        print(data['path'])
        img = Image.open(data['path'])
        img1 = Image.open('test_files/input/test150.jpg')
        print(img.size)
        print(img1.size)
        graph_shape = self.edit_doc.getGraphicObjects().getByName('$photo')
        print(graph_shape.getSize().Height)
        print(graph_shape.getSize().Width)

        img_with_border = self.resize_with_padding(img, (200, 200))
        img_with_border.save(data['path'] + '-border.png')
        fileurl = unohelper.systemPathToFileUrl(os.path.dirname(os.path.abspath(__file__)) + '/' + data['path'])
        graphic = self.graphicprovider.queryGraphic((PropertyValue('URL', 0, fileurl, 0), ))
        self.edit_doc.getGraphicObjects().getByName('$photo').Graphic = graphic

    def resize_with_padding(self, img, expected_size):
        img.thumbnail((expected_size[0], expected_size[1]))
        # print(img.size)
        delta_width = expected_size[0] - img.size[0]
        delta_height = expected_size[1] - img.size[1]
        pad_width = delta_width // 2
        pad_height = delta_height // 2
        padding = (pad_width, pad_height, delta_width - pad_width, delta_height - pad_height)
        return ImageOps.expand(img, padding, 'white')

    def convert_table(self, name, data):
        table = self.oWriterTables.getByName("$" + name)  # plante si on met pas de dollar, vu qu'il le vérifie
        # absolument pas et assume qu'un tableau contenant des variables est lui-même une variable
        rows = table.getRows()
        rows.insertByIndex(2, len(data))
        table_data = table.getDataArray()
        template = table_data[1]
        myarray = (table_data[0],)
        for (mydata) in data:
            tmp = template
            for (k, d) in mydata.items():
                tmp = tuple(map(lambda x: x.replace('$' + k, d), tmp))
            myarray = myarray + (tmp,)
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

    def add_embedded_image(self, url=None, width=None, height=None,
                           paraadjust=None):
        dpi = self.dpi
        scale = 1000 * 2.54 / float(dpi)
        doc = self.edit_doc
        cursor = doc.Text.createTextCursor()
        cursor.gotoEnd(False)
        try:
            fileurl = unohelper.systemPathToFileUrl(url)
            graphic = self.graphicprovider.queryGraphic((
                PropertyValue('URL', 0, fileurl, 0), ))
            if graphic.SizePixel is None:
                original_size = graphic.Size100thMM
            else:
                original_size = graphic.SizePixel
            graphic_object_shape = doc.createInstance(
                'com.sun.star.drawing.GraphicObjectShape')
            graphic_object_shape.Graphic = graphic
            if width and height:
                size = Size(int(width * scale), int(height * scale))
            elif width:
                size = Size(int(width * scale), int((
                    float(width) / original_size.Width) * original_size.Height * scale))
            elif height:
                size = Size(
                    int((float(height) / original_size.Height) * original_size.Width * scale), int(height * scale))
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
            if paraadjust:
                cursor.ParaAdjust = oldparaadjust
        except Exception as e:
            print(e)


def connect(host="localhost", port="2002"):
    local_context = uno.getComponentContext()
    servicemanager = local_context.ServiceManager
    resolver = servicemanager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context)
    context = resolver.resolve("uno:socket,host=%s,port=%s;urp;StarOffice.ComponentContext" % (host, port))
    desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)
    graphicprovider = context.ServiceManager.createInstance('com.sun.star.graphic.GraphicProvider')
    return desktop, graphicprovider


if __name__ == '__main__':
    p = configargparse.ArgumentParser(default_config_files=['config.ini'])
    p.add_argument('-c', '--config', is_config_file=True, help='config file path')
    p.add_argument('--host', required=True, help='host connection libreoffice')
    p.add_argument('--port', help='port')
    p.add_argument('--action', help='list or create')
    p.add_argument('input', nargs='?', default=sys.stdin)
    p.add_argument('-d', "--data", help='file with data in json put')
    p.add_argument('-f', '--file', default='test_files/input/test.odt', help='oo template')
    p.add_argument('-t', '--to_file', default='test_files/output/test1.odt', help='out file')
    options = p.parse_args()
    if options.action == "create":
        if options.data is not None:
            Io_f = open(options.data)
        else:
            Io_f = options.input
        datas = json.loads(Io_f.read())
        oo_connect = connect(options.host, options.port)
        oo_template = oo_template()
        oo_template.convert(oo_connect, options.file, datas, options.to_file)
    else:
        oo_connect = connect(options.host, options.port)
        oo_template = oo_template()
        oo_template.list_vars(oo_connect, options.file)
