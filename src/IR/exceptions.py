class ImportException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)

class ExportException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)

class TransformException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)

class NodeException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)