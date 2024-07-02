"""
The agent is nearly the top level item of the device
"""
from abc import ABC, abstractmethod
from protocol import Protocol
class Executive:
    def __init__(self, protocol: Protocol):

    def __call__(self, query: str)->str:



class Agent:
    """
    The agent operates by feeding information into a primary executive
    model and a series of assistant modules.
    """
    def register_module(self, module):
        self.modules.append(module)

    def query_module(self, module, command):
        pass

    def interaction_loop(self, initial_commentary):

        # Setup the initial
        feedback = initial_commentary
        while True:
            executive_directive = self.executive.query(feedback)
            try:
                commands = self.protocol.extract(executive_directive)

                responses = {}
                for module, command in commands.items():
                    tag = f"module: {module}, command: {command['command']}"

                    response = self.query_module(module, command)
                    response = self.protocol.convert(response)
                    responses[tag] = response

                feedback = []
                for tag, response in responses.items():
                    feedback.append(f"---- {tag} ----")
                    feedback.append(response)
                feedback = "\n".join(feedback)
            except Exception as err:
                feedback = str(err)
