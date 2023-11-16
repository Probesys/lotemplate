from com.sun.star.beans import PropertyValue, UnknownPropertyException
from com.sun.star.lang import XComponent
import regex
from urllib import request
from PIL import Image
from lotemplate.utils import get_file_url, is_network_based
from com.sun.star.awt import Size


class ImageStatement:
    image_regex = regex.compile(r'\$\w+')

    def scan_image(doc: XComponent) -> dict[str, dict[str, str]]:
        """
        scan for images in the given doc

        :param doc: the document to scan
        :return: the scanned variables
        """

        return {
            elem.LinkDisplayName[1:]: {'type': 'image', 'value': ''}
            for elem in doc.getGraphicObjects()
            if ImageStatement.image_regex.fullmatch(elem.LinkDisplayName)
        }

    def image_fill(doc: XComponent, graphic_provider, variable: str, path: str, should_resize=True) -> None:
        """
        Fills all the image-related content

        :param should_resize: specify if the image should be resized to keep his original size ratio
        :param graphic_provider: the graphic provider, from the established connection
        :param doc: the document to fill
        :param variable: the variable to search
        :param path: the path of the image to replace with
        :return: None
        """

        if not path:
            return

        for graphic_object in doc.getGraphicObjects():
            if graphic_object.LinkDisplayName != variable:
                continue

            new_image = graphic_provider.queryGraphic((PropertyValue('URL', 0, get_file_url(path), 0),))

            if should_resize:
                with Image.open(request.urlopen(path) if is_network_based(path) else path) as image:
                    ratio = image.width / image.height
                new_size = Size()
                new_size.Height = graphic_object.Size.Height
                new_size.Width = graphic_object.Size.Height * ratio
                graphic_object.setSize(new_size)

            graphic_object.Graphic = new_image

