"""
Commands

----- What is this module ----

This module concerns the defining and loading of commands.

A command is a specification in terms of a hierarchical syntax of
a function to be called and arguments for that function. It also consists of
a description of what the command can be used for and what module it should be
considered a part of. It is used to allow a LLM to access and use programmic resources.

---- Objectives of defining commands ----

With regards to the Command object, the objective will be to bind a command
schema to a python function, and display information on how that function is used.

The command must provide a manual on what it can do, how to use it, and what to avoid.

---- Objectives on loading commands ----

Loading in a list of commands elegantly and smoothly from a TOML file will be the objective
for loading commands. This will result in a list of COMMAND o

---- Objectives of defining commands  ---


The syntax of a command is, surprisingly, not defined by the command specification itself.
Instead, a later SyntaxParser module will be responsible for converting a
Command Intermediate Specification (CIS) into a format that the LLM module
using the commands is best suited to handle.

This means, in effect, the purpose of defining of a command is to do a few thingsL

- Define a schema for the command: This is how the command is invoked, and will be in CIS
- Define the function bindings for the command: This will be a python function in some file
    which is invoked by the command once it is run.
- Define

The command


"""

import toml
import string
from typing import Dict, Any, List
from dataclasses import dataclass


### Constants ###

SYNTAX_COMMAND_SCHEMA = "schema"
SYNTAX_RETURN_SCHEMA = "return"


### Exceptions ###


###

class SyntaxAST:
    """
    A object containing a representation of the
    syntax of a command. This varient is

    In stub form, the syntax Intermediate Command Schema: A Pytree


    """

class Manual:
    """
    A Manual feature.

    A manual is a string of text containing formatting referrences
    that must be defined in order for a command to load. It is used
    by the model to learn how to interact with the command.

    The manual object must refer
    """
    def find_dependencies(self, text: str)->List[str]:
        formatter = string.Formatter()
        dependencies = [item[1] for item in formatter.parse(text) if item[1] is not None]
        dependencies = list(set(dependencies))
        return dependencies

    def __init__(self, text: str):

        # Verify the manual contains the expected formatting references

        dependencies = self.find_dependencies(text)


        self.text = text
        self.dependencies =

        if "schema" not in self.dependencies:




@dataclass
class Example:
    name: str
    description: str
    syntax: Dict[str, Any]


class Command:
    """
    The command feature

    ---- fields ----

    module: What it is part of
    name: What it is
    description: How it works.
    syntax: How it's syntax works


    """

@dataclass
class Command:
    """
    The command feature.
    """
    name: str
    description: str
    syntax: Dict[str, Any]
    outcome: Dict[str, Any]


### Intermediate Schema Logic ###

### Commands ####
#
# Commands are the thing the model can actually demand happen. In this
# configuration file, we define these commands. These commands will
# later be read by the protocol instances and turned into examples
#
# These commands list their metainfo, then give a query schema and a return schema.
#
# The query schema tells us how to invoke the command, the return schema what the response
# will look like.

### Modules ###
#
# Modules are the top level feature of a command collection. They should be
# define in terms of
# - a "module_name" indicating what to call it
# - a "purpose" indicating what the module is for
# - any number of attached commands.

# They may have any number of attached commands

###
# Commands must be provided as a subclass on the module class that contains
# - a "command_name" feature that tells us what to call it
# - a "purpose" feature
# - a "query_schema" subfeature containing the hierarchial information to be dispatched in a query. The
#   query schema must contain a feature called "command" that indicates what the parse engine will dispatch to
#   and may contain other features as well.
# - a "response_schema" subfeature indicating how responses are expected to be returned.
#
# They will be loaded into and returned into a dictionary with the same features

required_module_keys = {"module_name", "module_command", "purpose"}


def validate_module_commands(module_dict):
    # Validate the module dictionary
    if not isinstance(module_dict, dict):
        return "Module must be a dictionary"

    # Validate module required fields
    if not all(key in module_dict for key in required_module_keys):
        return f"Module is missing required keys: {required_module_keys - module_dict.keys()}"

    if not isinstance(module_dict["module_name"], str):
        return "'module_name' must be a string"
    if not isinstance(module_dict["module_command"], str):
        return "'module_command' must be a string"
    if not isinstance(module_dict["purpose"], str):
        return "'purpose' must be a string"

    # Validate commands within the module
    for command_key, command_value in module_dict.items():
        if command_key in required_module_keys:
            continue

        if not isinstance(command_value, dict):
            return f"Command {command_key} must be a dictionary"

        # Validate command required fields
        required_command_keys = {"command_name", "purpose", "query_schema", "response_schema"}
        if not all(key in command_value for key in required_command_keys):
            return f"Command {command_key} is missing required keys: {required_command_keys - command_value.keys()}"

        if not isinstance(command_value["command_name"], str):
            return f"Command {command_key} 'command_name' must be a string"
        if not isinstance(command_value["purpose"], str):
            return f"Command {command_key} 'purpose' must be a string"

        # Validate query_schema
        query_schema = command_value["query_schema"]
        if not isinstance(query_schema, dict):
            return f"Command {command_key} 'query_schema' must be a dictionary"
        if "command" not in query_schema or not isinstance(query_schema["command"], str):
            return f"Command {command_key} 'query_schema.command' must be a string and present"
        if "module" not in query_schema or not isinstance(query_schema["module"], str):
            return f"Command {command_key} 'query_schema.module' must be a string and present"
        if query_schema["module"] != module_dict["module_command"]:
            return f"Command {command_key} 'query_schema.module' does not match module_command"

        # Validate response_schema
        response_schema = command_value["response_schema"]
        if not isinstance(response_schema, dict):
            return f"Command {command_key} 'response_schema' must be a dictionary"

    # If all checks pass
    return None

def load_commands_from_file(file) -> Dict[str, Any]:
    """
    Loads a list of available commands into a dictionary by loading them out of a
    TOML file.

    Commands must be defined in TOML as a class that contains
    - a "command_name" feature
    - a "purpose" feature
    - a "query_schema" subfeature containing the hierarchial information to be dispatched in a query
    - a "response_schema" subfeature indicating how responses are expected to be returned.

    They will be loaded into and returned into a dictionary with the same features
    """
    # Load commands
    with open(file, 'r') as f:
        commands = toml.load(f)

    # Validate commands
    for key, module_dict in commands.items():
        validation = validate_module_commands(module_dict)
        if validation:
            raise RuntimeError(f"Command with name '{key}' did not load properly: {validation}")

    # return results
    return commands

def iterate_commands(module_dict: Dict[str, Any]):
    """
    Iterates over commands in module dict
    :param module_dict: A module dict
    :return: The command
    """
    for key, command_dict in module_dict.items():
        if key in required_module_keys:
            continue
        yield command_dict

