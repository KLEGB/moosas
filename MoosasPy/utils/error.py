

class ShellError(Exception):
    def __init__(self, execution, message):
        self.execution = execution
        self.message = message

    def __str__(self):
        return f"{self.execution}: {self.message}"


class FileError(Exception):
    def __init__(self, file):
        self.file = file

    def __str__(self):
        return f"FileError, {self.file} is not a valid moosas file"

class GeometryError(Exception):
    def __init__(self,geometry,reason):
        self.geometry = geometry
        self.reason = reason

    def __str__(self):
        return f"GeometryError: {self.geometry} is invalid: {self.reason}"

class TopologyError(Exception):
    def __init__(self,func,reason):
        self.func = func
        self.reason = reason
    def __str__(self):
        return f"TopologyError: {self.func}, {self.reason}"
