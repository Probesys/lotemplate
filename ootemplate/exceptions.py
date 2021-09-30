"""
A class containing all necessaries exceptions with
custom attributes, useful for the API
"""


__all__ = ('err',)


class Errors:
    class JsonException(Exception):
        def __init__(self, message, file):
            self.json_file = file
            super().__init__(message)

    class JsonInvalidBaseValueType(JsonException):
        def __init__(self, message, file, variable_type):
            super().__init__(message, file)
            self.variable_type = variable_type

    class JsonEmptyBase(JsonException):
        pass

    class JsonInstanceException(JsonException):
        def __init__(self, message, file, instance):
            super().__init__(message, file)
            self.instance = instance

    class JsonInvalidInstanceValueType(JsonInstanceException):
        def __init__(self, message, file, instance, variable_type):
            super().__init__(message, file, instance)
            self.variable_type = variable_type

    class JsonEmptyInstance(JsonInstanceException):
        pass

    class JsonVariableError(JsonInstanceException):
        def __init__(self, message, variable: str, json: str, instance):
            super().__init__(message, json, instance)
            self.variable = variable

    class JsonInvalidValueType(JsonVariableError):
        def __init__(self, message, variable: str, json: str, instance, variable_type):
            super().__init__(message, variable, json, instance)
            self.variable_type = variable_type

    class JsonImageError(JsonInstanceException):
        def __init__(self, message, image: str, json: str, instance):
            super().__init__(message, json, instance)
            self.image = image

    class JsonImageEmpty(JsonImageError):
        pass

    class JsonImageInvalidArgument(JsonImageError):
        def __init__(self, message, image: str, json: str, instance, argument):
            super().__init__(message, image, json, instance)
            self.argument = argument

    class JsonImageInvalidArgumentType(JsonImageInvalidArgument):
        def __init__(self, message, image: str, json: str, instance, argument, variable_type):
            super().__init__(message, image, json, argument, instance)
            self.variable_type = variable_type

    class JsonImageInvalidPath(JsonImageError):
        def __init__(self, message, image, json, instance, path):
            super().__init__(message, image, json, instance)
            self.path = path

    class JsonTableError(JsonInstanceException):
        def __init__(self, message, table: str, json: str, instance):
            super().__init__(message, json, instance)
            self.table = table

    class JsonInvalidTableValueType(JsonTableError):
        def __init__(self, message, table: str, json: str, instance, variable: str, variable_type: str):
            super().__init__(message, table, json, instance)
            self.variable = variable
            self.variable_type = variable_type

    class JsonInvalidRowValueType(JsonInvalidTableValueType):
        def __init__(self, message, table: str, json: str, instance, variable: str, variable_type: str, row):
            super().__init__(message, table, json, instance, variable, variable_type)
            self.row = row

    class JsonEmptyTable(JsonTableError):
        pass

    class JsonEmptyTableVariable(JsonEmptyTable):
        def __init__(self, message, table, json, instance, variable):
            super().__init__(message, table, json, instance)
            self.variable = variable

    class TemplateException(Exception):
        def __init__(self, message, file):
            super().__init__(message)
            self.file = file

    class TemplateDuplicatedVariable(TemplateException):
        def __init__(self, message, file, variable, first_type, second_type):
            super().__init__(message, file)
            self.variable = variable
            self.first_type = first_type
            self.second_type = second_type

    class TemplateVariableNotInLastRow(TemplateException):
        def __init__(self, message, file, table, row, expected_row, variable):
            super().__init__(message, file)
            self.table = table
            self.actual_row = row
            self.expected_row = expected_row
            self.variable = variable

    class TemplateInvalidFormat(TemplateException):
        def __init__(self, message, template, document_format):
            super().__init__(message, template)
            self.document_format = document_format

    class JsonComparaisonException(Exception):
        def __init__(self, message, json, instance, template):
            self.template_file = template
            self.json_file = json
            self.instance = instance
            super().__init__(message)

    class JsonComparaisonVariableError(JsonComparaisonException):
        def __init__(self, message, variable: str, json: str, instance, _template: str):
            super().__init__(message, json, _template, instance)
            self.variable = variable

    class JsonMissingRequiredVariable(JsonComparaisonVariableError):
        pass

    class JsonMissingTableRequiredVariable(JsonMissingRequiredVariable):
        def __init__(self, message, variable: str, json: str, instance, _template: str, table):
            super().__init__(message, variable, json, instance, _template)
            self.table = table

    class JsonUnknownVariable(JsonComparaisonVariableError):
        pass

    class JsonIncorrectValueType(JsonComparaisonVariableError):
        def __init__(self, message, variable, json, instance, template, expected_variable_type, actual_variable_type):
            super().__init__(message, variable, json, instance, template)
            self.actual_variable_type = actual_variable_type
            self.expected_variable_type = expected_variable_type

    class JsonUnknownTableVariable(JsonUnknownVariable):
        def __init__(self, message, variable: str, json: str, instance, _template: str, table):
            super().__init__(message, variable, json, instance, _template)
            self.table = table

    class ExportException(Exception):
        def __init__(self, message, file):
            super().__init__(message)
            self.file = file

    class ExportInvalidFormat(ExportException):
        def __init__(self, message, file, document_format):
            super().__init__(message, file)
            self.document_format = document_format

    class ExportUnknownError(ExportException):
        def __init__(self, message, file, exception):
            super().__init__(message, file)
            self.exception = exception

    class FileNotFoundError(Exception):
        def __init__(self, message, file):
            super().__init__(message)
            self.file = file

    class UnoException(Exception):
        def __init__(self, message, host, port):
            super().__init__(message)
            self.host = host
            self.port = port

    class UnoBridgeException(UnoException):
        def __init__(self, message, host, port, file):
            super().__init__(message, host, port)
            self.file = file

    class UnoConnectionError(UnoException):
        pass

    class UnoConnectionClosed(UnoConnectionError):
        pass


err = Errors()
