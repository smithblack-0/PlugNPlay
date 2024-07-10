from typing import Dict, List, Any, Callable
from src.irnodes import IRSchemaNode



class FunctionStub:
    name: str
    user_manual: str
    user_examples: Dict[str, IRSchemaNode]
    docstring: str
    syntax: IRSchemaNode
    command_binding: Callable
class ModuleStub:
    name: str
    user_manual: str
    functions: List[str, FunctionStub]