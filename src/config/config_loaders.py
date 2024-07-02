"""
Utility functions to load config entities

"""

from typing import Dict, Any
from config_utilities import load_commands_from_file

def load_commands()->Dict[str, Any]:
    """
    Loads in a dictionary of basic commands from the appropriate config file.
    """
    return load_commands_from_file("../modules/base/commands.TOML")
