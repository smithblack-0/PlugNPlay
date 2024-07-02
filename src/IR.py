"""
Contains the Intermediate Representation command
binding encodings for communications between models
and between models and resources.
"""
import textwrap
from typing import Protocol, Set, Dict, Any, Callable, Optional
from dataclasses import dataclass
import string
import jsonschema

IR_PYTREE_FORMAT = Dict[str, Any]

### Exceptions

class IRError(Exception):
    def __init__(self, msg: str, code: str):
        self.msg = msg
        self.code = code
        super.__init__(msg)

class IRValidationError(IRError):
    pass

class Schema:
    """
    An object representing the schema
    that a command must obey in the
    JSON intermediate language.

    ---- fields ----

    schema: A IR representation of the rule's schema

    ---- methods ----

    check: Returns true or false if the schema and rule match
    validate: Throws if the schema does not match.
    """
    def __init__(self,
                 schema: Dict[str, Any],
                 ):


        self.schema = schema

    def check(self, ir: IR_PYTREE_FORMAT):
        """
        Validate if the given ir matches the schema. Returns
        true if yes, false if no.

        :param ir: The IR to check
        :return: True if matching, false if not.
        """
        try:
            jsonschema.validate(ir, self.schema)
            return True
        except jsonschema.exceptions.ValidationError:
            return False

    def validate(self, ir: IR_PYTREE_FORMAT):
        jsonschema.validate(ir, self.schema)


class Manual:
    """
    An unformatted page that contains information needed
    for final formatting of a LLM manual.

    ---- Defining a manual ----

    A manual is, broadly speaking, defined in terms of several things.
    These are, broadly speaking:

    - A formatting template that has the majority of the situations information already displayed,
      with the exception of displaying exact syntax for things like commands.
    - A dictionary mapping formatting requirements to IR examples or schemas. Optional, but
      usually used.
    - Optionally, a Schema, in which case there is expected to be a {schema} formatting
      feature in the manual and all examples must match the schema.


    The purpose of this arrangement is to allow the dynamic conversion of the
    syntax into the local display language favored by the model, to allow a
    truly universal plug-n-play mechanism

    ---- fields ----

    manual: The unformatted manual template
    examples: Examples in IR spec that need to be converted for display

    ---- methods ----

    get_examples: Gets the examples in the local IR specification
    get_manual: Given formatted examples, gives the manual
    """
    def get_examples(self)->Dict[str, IR_PYTREE_FORMAT]:
        """
        Get and return all
        :return:
        """

    def extract_dependencies(self, text: str)->Set[str]:
        """Extract formatting dependencies using python's library"""
        formatter = string.Formatter()
        dependencies = [item[1] for item in formatter.parse(text) if item[1] is not None]
        dependencies = set(dependencies)
        return dependencies


    def __init__(self,
                 manual: str,
                 examples: Optional[Dict[str, IR_PYTREE_FORMAT]]
                 ):

        if examples is None:
            examples = {}

        has_schema = False
        if schema is not None:
            has_schema = True
            self.validate_schema_in_manual(manual)
            examples["schema"] = schema.schema

        dependencies = self.

        self.manual = manual
        self.schema = [schema.schema if schema is not None else None]
        self.examples = examples

class ResourceInterface:
    """
    The manual stub. Contains all information besides
    special syntax cases that need to be converted
    in order to render a manual.

    Much of the displayed information exists to be processed
    by later classes before manual display.

    ---- fields ----

    dependencies: Names of formatting dependencies that must be provided
    manual: An unformatted manual page. The manual page
    syntax: An IR representing the syntax.
    binding: A python binding to invoke when using the command
    examples: examples with syntax in json IR representation

    ---- methods ----

    get_manual: Passed a formatting dictionary, will return the manual on how to use the command
    invoke_command: Passed a python binding,
    """


    def

class CommandStub:
    """
    The individual command

    Information needed:

    - Command binding
    - IR Syntax
    - IR Examples
    - Unformatted Manual

    Validation needed:

    - Ensure {syntax} is displayed in the manual page
    - Ensure for each named example {example} is displayed in the manual page
    - Ensure command binding exists.
    - Ensure manual exists
    """

class ModuleStub:
    """
    A stub for an entire module


    """