"""
A class containing all necessaries exceptions with
custom attributes, useful for the API
"""


__all__ = (
    'LotemplateError',
    'JsonSyntaxError',
    'TemplateError',
    'JsonComparaisonError',
    'ExportError',
    'FileNotFoundError',
    'UnoException',
)

from typing import Union


class LotemplateError(Exception):
    def __init__(self, code: str, message: str, infos: dict[str: Union[str, int]]):
        super().__init__(message)
        self.code = code
        self.infos = infos


class JsonSyntaxError(LotemplateError):
    pass


class TemplateError(LotemplateError):
    pass


class JsonComparaisonError(LotemplateError):
    pass


class ExportError(LotemplateError):
    pass


class FileNotFoundError(LotemplateError):
    pass


class UnoException(LotemplateError):
    pass
