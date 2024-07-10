import unittest
from typing import Any, Union, List, Dict
from src.irnodes import IRNodeError, SchemaGroup
from src.pybindings.loading_util import convert_type_to_schema, extract_schemagroup_from_function

SHOW_ERROR_MESSAGES = True

class TestConvertTypeToSchema(unittest.TestCase):
    """
    Unit tests for the convert_type_to_schema function.
    These tests cover basic and nested valid and invalid cases for type hints.
    """

    def validate(self, validator_func, value, should_pass=True):
        try:
            result = list(validator_func(value))
            if not should_pass:
                self.fail(f"{validator_func.__name__} did not raise PyTreeError as expected")
            return result
        except IRNodeError as e:
            if should_pass:
                if SHOW_ERROR_MESSAGES:
                    self.fail(f"{validator_func.__name__} raised PyTreeError unexpectedly: {e}")
                else:
                    self.fail(f"{validator_func.__name__} raised PyTreeError unexpectedly!")
            else:
                if SHOW_ERROR_MESSAGES:
                    print(f"Expected PyTreeError: {e}")
            return None

    def test_basic_types(self):
        type_hints = [int, float, str, bool, Any]
        expected_schemas = [int, float, str, bool, Any]

        for type_hint, expected_schema in zip(type_hints, expected_schemas):
            schemas = self.validate(convert_type_to_schema, type_hint)
            self.assertEqual(schemas, [expected_schema])

    def test_union_type(self):
        type_hint = Union[int, str]
        expected_schemas = [int, str]

        schemas = self.validate(convert_type_to_schema, type_hint)
        self.assertEqual(schemas, expected_schemas)

    def test_list_type(self):
        type_hint = List[int]
        expected_schemas = [[int]]

        schemas = self.validate(convert_type_to_schema, type_hint)
        self.assertEqual( expected_schemas, schemas)

    def test_dict_type(self):
        type_hint = Dict[str, int]
        expected_schemas = [{str : int}]

        schemas = self.validate(convert_type_to_schema, type_hint)
        self.assertEqual(expected_schemas, schemas)

    def test_nested_union_type(self):
        type_hint = Union[List[int], Dict[str, int]]
        expected_schemas = [[int], {str : int}]

        schemas = self.validate(convert_type_to_schema, type_hint)
        self.assertEqual(schemas, expected_schemas)

    def test_invalid_type(self):
        self.validate(convert_type_to_schema, object, should_pass=False)




class TestExtractSchemagroupFromFunction(unittest.TestCase):
    """
    Unit tests for the extract_schemagroup_from_function function.
    These tests cover the extraction of type hints and their conversion into schemas.
    """

    def test_extract_schemagroup_from_simple_function(self):
        def simple_function(a: int, b: float) -> str:
            return "result"

        schema_group = extract_schemagroup_from_function(simple_function, name="simple_group", priority=0)

        self.assertIsInstance(schema_group, SchemaGroup)
        self.assertEqual(schema_group.name, "simple_group")
        self.assertEqual(schema_group.priority, 0)

    def test_extract_schemagroup_from_complex_function(self):
        def complex_function(a: int, b: List[Union[str, int]]) -> Dict[str, int]:
            return {"example": 1}

        schema_group = extract_schemagroup_from_function(complex_function, name="complex_group", priority=1)

        self.assertIsInstance(schema_group, SchemaGroup)
        self.assertEqual(schema_group.name, "complex_group")
        self.assertEqual(schema_group.priority, 1)

    def test_extract_schemagroup_from_function_with_default_return(self):
        def default_return_function(a: int) -> Any:
            return a

        schema_group = extract_schemagroup_from_function(default_return_function, name="default_return_group",
                                                         priority=2)

        self.assertIsInstance(schema_group, SchemaGroup)
        self.assertEqual(schema_group.name, "default_return_group")
        self.assertEqual(schema_group.priority, 2)

    def test_extract_schemagroup_from_function_with_no_return(self):
        def no_return_function(a: int):
            pass

        schema_group = extract_schemagroup_from_function(no_return_function, name="no_return_group", priority=3)

        self.assertIsInstance(schema_group, SchemaGroup)
        self.assertEqual(schema_group.name, "no_return_group")
        self.assertEqual(schema_group.priority, 3)
