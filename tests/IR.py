import unittest
from src.IR import IRValidationError, Schema

PRINT_ERROR_MESSAGES = True

class test_Schema(unittest.TestCase):
    """
    Test the schema mechanism. Make sure it works.
    """
    def setUp(self) -> None:
        example_schema = {
          "$schema": "http://json-schema.org/draft-07/schema#",
          "type": "object",
          "properties": {
            "command": {
              "type": "object",
              "properties": {
                "make_subagent": {
                  "type": "string"
                }
              },
              "required": ["make_subagent"],
              "additionalProperties": False
            },
            "modules": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["command", "modules"],
          "additionalProperties": False
        }

    def test_bad_schema(self):
        """Test we throw an appropriate error """
        with self.assertRaises(IRValidationError) as err:
            schema = Schema(open)
        self.assertEqual(err.exception.code , "Bad Schema")
        if PRINT_ERROR_MESSAGES:
            print(err.exception)

    def test_nonmatching_ir(self):
        """Test we can detect when the IR does not match the schema"""
        raise NotImplementedError()

    def test_validate_ir_throws(self):
        """ Test we throw when using the validate feature and the IR does not match the schema"""
        raise NotImplementedError()

class testManual:
    """
    Test the manual mechanism
    """
    def test_manual_get_examples(self):
        """ Test we are reciving out the same examples we put in"""
        raise NotImplementedError()

    def test_manual_format_manual(self):
        """
        Test that when we provide the needed dependencies, the class will format
        us a manual
        """

class testCommandBinding:
    """
    Test the command binding mechanism. This should be utilized to connect a
    command to associated code.
    """
    def test_display_docstring(self):
        """ Test we properly extract the docstrings"""

    def test_invoke(self):
        """ Test we can invoke the binding"""

    def test_throw_no_type_hints(self):
        """Test we throw when the function we are handed did not have type hints"""

    def test_misaligned_schema(self):
        """
        Test we get an exception when invoking a co happens when the schema
        and function typehints are misaligned.
        """


class testResource:
    """
    Test the command unit, which puts everything together into a cohesive
    whole.
    """
