"""
A class containing all necessaries exceptions with
custom attributes, useful for the API
"""


__all__ = (
    'OotemplateError',
    'JsonSyntaxError',
    'TemplateError',
    'JsonComparaisonError',
    'ExportError',
    'FileNotFoundError',
    'UnoException',
)

from typing import Union


class OotemplateError(Exception):
    def __init__(self, message, infos: dict[str: Union[str, int]]):
        super().__init__(message)
        self.infos = infos


class JsonSyntaxError(OotemplateError):
    pass


class TemplateError(OotemplateError):
    pass


class JsonComparaisonError(OotemplateError):
    pass


class ExportError(OotemplateError):
    pass


class FileNotFoundError(OotemplateError):
    pass


class UnoException(OotemplateError):
    pass
