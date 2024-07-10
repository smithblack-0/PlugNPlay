import inspect
import string
import requests
from dataclasses import dataclass
from typing import Callable, Dict, Optional, List
from . import irnodes

from .text_extraction import TextExtractor

# Manual stub #
class TextIRStub:
    """
    A section of text and formatting features that belong with it.

    This contains both text with formatting features, and a dictionary
    of str to IRNodes that correlates with it.

    ---- fields ---
    name: name of this block of text.
    text_template: Exactly what it says on the tin. Has formatting entries
    ir_elements: Dictionary of formatting key to ir nodes.

    ---- methods ----
    ___init___: creates the stub
    __call__: When provided with a node convert function, will use it to format the strign
    """

    def __init__(self,
                 name: str,
                 unformatted_text: str,
                 ir_elements: Optional[Dict[str, irnodes.IRSchemaNode]] = None,
                 ):
        """
        :param unformatted_text: The unformatted text
        :param ir_elements: The ir elements
        :raise: TypeError - if there is an issue with type on any parameter
        :raise: ValueError - if the formatting features and dictionary keys do not match.
        """

        # Type validation
        if not isinstance(name, str):
            raise TypeError("'name' was not a string")
        if not isinstance(unformatted_text, str):
            raise TypeError("'unformatted_text' was not string")
        if not ir_elements is None:
            if not isinstance(ir_elements, dict):
                raise TypeError("'ir_elements' was not a dict")
            for key, value in ir_elements.items():
                if not isinstance(key, str):
                    raise TypeError(f"key '{key}' of 'ir_elements' was not string")
                if not isinstance(value, irnodes.IRSchemaNode):
                    raise TypeError(f'value was not an {irnodes.IRSchemaNode}')

        # formatting validation
        formatter = string.Formatter()
        arguments = [ item for _, item, _, _ in formatter.parse(unformatted_text)]
        if arguments != list(ir_elements.keys()):
            raise ValueError("Format elements in text and keys in dictionary do not match")

        self.name = name
        self.text_template = unformatted_text
        self.ir_elements = ir_elements


### Tools and toolboxes ###


class ToolStub:
    """
    A tool stub contains a collection of manual pages,
    a call syntax representation and a python call binding.
    """

    # Utility methods
    @staticmethod
    def extract_function_schema(function: Callable)->Dict[str, irnodes.IRSchemaNode]:
        function_name = function.__name__
        sig = inspect.signature(function)

        params = {}
        for name, parameter in sig.parameters.items():
            if parameter.annotation is inspect.Parameter.empty:
                raise ValueError("Cannot convert functions that do not have completely defined typehints")
            params[name] = irnodes.type_hint_to_schema(parameter.annotation)

        parameters = irnodes.pytree_to_schema(params),
        _return = irnodes.type_hint_to_schema(sig.return_annotation)
        return function_name, parameters, _return

    @staticmethod
    def extract_function_docstring(function: Callable)->str:
        return inspect.getdoc(function)

    # Init #
    def __init__(self,
                 name: str,
                 call_binding: Callable,
                 _manuals: Optional[Dict[str, TextIRStub]] = None
                 ):
        # Get
        function_name, parameters, _return = self.extract_function_schema(call_binding)
        docstring = self.extract_function_docstring(call_binding)

        self.name = name
        self.function_name = name
        self.manuals = {"docstring" : TextIRStub("docstring", docstring)}
        self.call_syntax = parameters
        self.return_syntax = _return
        self.call_binding = call_binding

    # Manual registration methods #

    def register_manual_page(self, page: TextIRStub):
        """
        Registers a manual page.

        :param page: The manual page to register
        """
        if page.name in self.manuals:
            raise KeyError("Page with name {page.name} already in manuals")
        self.manuals[page.name] = page

    def register_manual_string(self,
                                name: str,
                                manual: str,
                                examples: Optional[Dict[str, irnodes.PyTree]] = None
                                ):
        """
        Registers a manual using a name and passed examples

        :param name: The name of the manual page
        :param manual: The manual string
        :param examples: The formatting examples in terms of a pytree. Optional.
        """
        page = TextIRStub(name, manual, examples)
        self.register_manual_page(page)

    def register_manual_filedump(self,
                              name: str,
                              file: str
                              ):
        """
        Registers a manual page from a text or textlike file by
        dumping the information into a manual page.

        :param name: The name to call the manual page
        :param file: The file to dump from
        """
        with open(file) as f:
            data = f.read()
        page = TextIRStub(name, data)
        self.register_manual_page(page)
    def register_manual_link(self,
                              name: str,
                              link: str
                              ):
        """
        Registers a manual page by pulling from a link by getting a requests of
        it.

        :param name: The name to call the page
        :param link: The link to dump from
        """
        response = requests.get(link)
        if response.status_code != 200:
            raise RuntimeError("Request code was not 200")
        page = TextIRStub(name, response.content)
        self.register_manual_page(page)

    # Manual transformation methods
    def transform_manuals(self,
                          function: Callable[[TextIRStub], TextIRStub]
                          )->'ToolStub':
        """
        Transform all present manuals, then return a new toolstub
        instance with the transforms present.

        :param function: The transformation function. It must accept and return
                         a TextIRStub. IT will be applied to all manual pages.
        :return: A new toolstub with updated manuals
        """
        new_manuals = {}
        for key, value in self.manuals.items():
            new_manuals[key] = function(value)
        return ToolStub(self.name, self.call_binding, new_manuals)

    # Toml Language

class ToolBox:
    """
    A combination of a builder to create a toolbox.

    Allows for the registration of manual features
    and various tools.
    """

    def register_module_manual(self,
                               text: str,
                               examples: Optional[Dict[str, irnodes.PyTree]]
                               ):

    def register_tool(self, name: str, function: Callable):
    def __init__(self, toolbox_name: str):
        self.name = toolbox_name
        self.module_manuals: Dict[str, TextIRStub] = {}
        self.tools: Dict[str, ToolStub] = {}

class Toolbox:

    # Registration logic #


    def register(self,
                 name: str,
                 ):
        """
        A decorator designed to allow registration of a function
        or method to a particular toolbox. Requires a name parameter.

        :param name: The name to call the tool we are registering.
        :return: A callable designed to be called with the function to register.
        """

        def registration_closure(function: Callable):
            docstring_manual = self.extract_function_docstring(function)
            docstring_manual = TextIRStub("docstring_extract", docstring_manual, None)
            syntax = self.extract_function_schema(function)
            self.tools[name] = ToolStub(name, [docstring_manual], syntax, function)

        return registration_closure

    # Extensions
    def add_module_manual(self, manual: str, examples: Optional[Dict[str, irnodes.PyTree]] = None):
        """
        Register an additional manual feature.
        :param manual:
        :param examples:
        :return:
        """

    def add_tool_manual


    def __init__(self,
                 manuals: str | List[str] | None
                 ):
        self.module_manuals = []
        self.tools: Dict[str, ToolStub] = {}


