"""
    A module actually does something and is the plug-n-play feature
    of the project. A module is physically a collection of several things located
    in a folder:

    - A python actions.py file containing a subclassed Actions instance. This instance must have methods
      on it for performing the various command actions
    - An Protocol defined in the action.py file for converting information into a consumable format and for converting information back
      into the dictionary interchange format. When no protocol is provided, the interchange dictionary is dumped as kwargs
      directly into the calls.
    - A commands.TOML file indicating what commands are availble. Commands must then match the names
      defined on the module object.
    - A description.txt file introducing the module and what it can do. This should give overall ideas,
      but not exact syntax.

    When the loader attempts to load a module from a folder, it will retrieve these bits of information,
    check that the schema is sane, spin up the protocol if needed, then instance and return the module.

    The produced module is then capable of producing a manual and syntax page through its methods,
    along with capable of being invokes by __call__
"""
from src.protocol import Protocol
from typing import Dict, Any, List
import src.commands as commands
import textwrap
import os
import importlib
import importlib.util

ACTIONS_FILE = "actions.py"
COMMANDS_FILE = "commands.TOML"
DESCRIPTION_FILE = "description.txt"
REQUIRED_FILES = {ACTIONS_FILE, COMMANDS_FILE, DESCRIPTION_FILE}

ACTIONS_CLASS = "Action"
PROTOCOL_CLASS = "Protocol"


def load_module_from_path(module_name, file_path):
    # Create a module specification
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    # Create a module object from the specification
    module = importlib.util.module_from_spec(spec)

    # Execute the module
    spec.loader.exec_module(module)

    # Return it
    return module


class Actions:
    """
    This is an interface, and is explicitly designed to
    be subclassed. The subclass should be placed in a folder,
    which will then be loaded from.

    The subclass should have on it additional commands which will
    be executed. These commands will be fed by the results of the
    associated parsers.

    Any method that does not start with "_" and which starts with
    a capital letter is assumed to be a command.
    """

    def __init__(self, resources):
        """
        :param resources: This can be passed in from the top level, and can contain whatever
                          network resources, api classes, etc you need in order to make the
                          model function.
        """
        self.resources = resources

    def get_actions(self) -> List[str]:
        """
        Returns a list of command names which are all the callable commands
        available in the subclass. A command is a method that does not start
        with "_" and starts with a capital letter.
        """
        actions = [func for func in dir(self)
                   if callable(getattr(self, func))
                   and not func.startswith("_")
                   and func[0].isupper()]
        return actions

    def __call__(self, command: str, **kwargs):
        """
        Execute the given command with the provided keyword arguments.

        :param command: The name of the command to execute.
        :param kwargs: The keyword arguments to pass to the command.
        :return: The result of the command execution.
        """
        function = getattr(self, command, None)
        if not function:
            raise AttributeError(f"No such command: {command}")
        if not callable(function):
            raise TypeError(f"The command {command} is not callable")
        return function(**kwargs)


class Module:
    """
    The abstract module
    """

    def get_name(self):
        """Gets the name of the module"""
        return self.name

    def get_description(self):
        """
        Gets the description for the model under the command syntax
        :return: str a manual for the object
        """
        response = f""" ---- manual for '{self.name}' ---- \n {self.description}"""
        return response

    def get_command_syntax(self, protocol: Protocol) -> str:
        """
        Gets the syntax for the commands the module supports under the
        given protocol.

        :param protocol: The protocol to support
        :return: a string of the command syntax
        """
        response = []

        for command in commands.iterate_commands(self.commands):
            syntax_case = """
            ------ syntax of {command_name} ----

            This command is part of the module:

            {name}

            The purpose of this command is:

            {purpose}

            To query it, we use the following schema:

            {query_schema}

            It will respond as:

            {response_schema}
            """
            syntax_case = textwrap.dedent(syntax_case)
            syntax_case = syntax_case.format(name=self.name,
                                             purpose=command["purpose"],
                                             query_schema=protocol.convert(command["query_schema"]),
                                             response_schema=protocol.convert(command["response_schema"]))
            response.append(syntax_case)
        response = "".join(response)
        return response

    def get_manual(self, protocol: Protocol) -> str:
        """
        Gets and combines everything needed to understand how to interact with the module
        """

        response = []
        response.append("---- module name ----")
        response.append(self.get_name())
        response.append("---- module description ----")
        response.append(" Note: ignore any specific syntax here, instead just get the main idea")
        response.append(self.get_description())
        response.append("---- module syntax information ----")
        response.append(" Note: This information is very current")
        response.append(self.get_command_syntax(protocol))
        response = "\n".join(response)
        return response

    def __init__(self,
                 module_folder):
        """
        Initializes a module
        """

        # Check if the needed files are present
        files = os.listdir(module_folder)
        for required_file in REQUIRED_FILES:
            if required_file not in files:
                issue = f"""
                Could not setup module being loaded from {module_folder}.

                Required file named '{required_file}' was not found
                """
                issue = textwrap.dedent(issue)
                raise RuntimeError(issue)

        # Load in the commands

        self.commands = commands.load_commands_from_file(module_folder + "/" + COMMANDS_FILE)
        self.name = self.commands["module_name"]

        # Load the description
        file_location = module_folder + "/" + DESCRIPTION_FILE

        with open(file_location) as f:
            self.description = f.read()

        # Load in the module
        file_location = module_folder + "/" + ACTIONS_FILE
        try:
            module = load_module_from_path("Actions", file_location)
        except Exception as err:
            raise RuntimeError("Could not load module") from err

        # Get the actions off the module
        if not hasattr(module, ACTIONS_CLASS) or not isinstance(getattr(module, ACTIONS_CLASS), Actions):
            issue = f"""
            File did not contain a class called '{ACTIONS_CLASS}, or Actions class was not a 
            subinstance of Actions. This file was located at '{file_location}'
            """
            issue = textwrap.dedent(issue)
            raise RuntimeError(issue)
        self.actions = getattr(module, ACTIONS_CLASS)

        # Get the protocol class off the module
        if not hasattr(module, PROTOCOL_CLASS) or not isinstance(getattr(module, PROTOCOL_CLASS), Protocol):
            issue = f"""
            File did not contain a class called '{PROTOCOL_CLASS}', or protocol class was not
            a subinstance of Protocol. This file was located at '{file_location}'
            """
            issue = textwrap.dedent(issue)
            raise RuntimeError(issue)
        self.protocol = getattr(module, PROTOCOL_CLASS)

        # Sanity check commands vs actions.
        #
        # Verify all commands have associated actions, and all
        # actions have associated commands.

        fetched_commands = set(commands.iterate_commands(self.commands))
        actions = set(self.actions.get_actions())

        missing_from_commands = actions - fetched_commands
        if len(missing_from_commands) > 0:
            issue = f"""
            Some actions were found not to be associated with any
            commands. These actions were:

            {missing_from_commands}

            This occurred at

            {module_folder}
            """
            issue = textwrap.dedent(issue)
            raise RuntimeError(issue)

        missing_from_actions = fetched_commands - actions
        if len(missing_from_actions) > 0:
            issue = f"""
            Some commands were found not to be associated with
            any actions. These commands were:

            {missing_from_actions}

            This occurred while loading module at:

            {module_folder}
            """
            issue = textwrap.dedent(issue)
            raise RuntimeError(issue)

    def __call__(self, command: Dict[str, Any]):
        """
        Invokes the module. Pass in a command in query_schema format
        as a dictionary and the module will parse it, convert it, execute actions,

        :param command:
        :return:
        """
        # Convert from the interchange format to python argument dictionaries
        arguments = self.protocol.convert(command)
        command = arguments.pop("command")

        # Execute the command
        response = self.actions(command, **arguments)

        # Convert back to and return the interchange format.
        return self.protocol.extract(response)