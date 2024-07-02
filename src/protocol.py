"""
The protocol module contains the information on protocol parsing
needed to extract data out of a text string and/or convert to the appropriate format.

Internally, hierarchial data travels around the model as json but is converted to one
of the supported formats on the fly when reaching a module or the executive.

"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


### Commands : What the model can actually order to happen. These will
class Protocol(ABC):
    """
    The protocol class contains parsers for extracting issued informaton
    from a text stream and converters to convert extracted information into the
    apppropriate format.

    Importantly, it also is responsible for displaying information on how to use the protocol
    to the model that is consuming it.
    """

    #### Root command ####




    @abstractmethod
    def schema_converter(self, str)->str:
        """
        A very important abstract function, this will
        :param str:
        :return:
        """


    @abstractmethod
    def get_manual(self)->str:
        """
        Returns a manual indicating how to use the protocol
        """
    @abstractmethod
    def extract(self, string: str)->List[str]:
        """
        Parses a string, extracts information, and returns a list of hierarchical data in
        JSON format.
        """
    @abstractmethod
    def convert(self, string: str)->str:
        """
        Parses a JSON string and turns it back into the particular protocol of concern
        """

    def __init__(self, commands : Dict[str, Any]):
        self.commands = commands

class ProtocolParser:
    pass