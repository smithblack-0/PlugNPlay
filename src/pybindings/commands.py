from typing import Callable, Tuple, List, Dict



class FunctionManual:
    """
    Container for data related to rendering a manual

    ---- gpt instructions ----
    where present, type must be satisfied.
    user_manual may have formatting keys, these must match the keys in user examples
    typehint s

    """
    name: str
    user_manual: str
    user_examples: Dict[str, "Pytree"]
    docstring: str
    typehint_syntax: "Pytree"
    def __init__(self,
                 name: str,

                 ):


class CommandData:
    """
    Container and validation for command backend

    A command needs to be able to store how to use the command,
    the name of the command, and the pybinding

    """
    name: str
    manual: Tuple[str, Dict[str, "PyTree"]]
    pybinding: Callable


class Command:
    """
    A command object represents a bundle of information on
    a python binding and how to use it.

    ---- fields ----

    name: The name of the command
    manual: A feature representing the manual in IR format.
            Format
    """
