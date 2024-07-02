
from abc import ABC, abstractmethod

class Parser(ABC):
    """
    The parser class contains parsers for extracting issued informaton
    from a text stream into the json interchange format, or converting information
    from the json interchange format back into the text stream
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