import unittest
from typing import Any, Union
from src.pybindings.pytrees import LiteralNode, IntNode, BoolNode, StrNode, FloatNode, IRSchemaNode, AbstractType
from src.pybindings.pytrees import AbstractIntNode, AbstractBoolNode, AbstractStrNode, AbstractFloatNode
from src.pybindings.pytrees import BranchNode, DictNode, ListNode
from src.pybindings.pytrees import LiteralNode, AbstractIntNode, AbstractStrNode, AbstractDictNode, AbstractListNode, UnionNode, IRSchemaNode
from src.pybindings.pytrees import is_pytree_branch, is_pytree_leaf, is_schema_leaf
from src.pybindings.pytrees import validate_pytree, validate_pytree_schema, PyTreeError
from src.pybindings.pytrees import FormalSchema, SchemaGroup, SchemaRegistry


SHOW_ERROR_MESSAGES = True

### Node tests ###
# One important factor in pytrees is the intermediate language used to store
# a tree.
#
# This section contains tests for it.

class TestIRSchemaNodeRegistry(unittest.TestCase):
    """
    Unit tests for IRSchemaNode registry logic.
    These tests cover:
    - Registration and retrieval of literal nodes
    - Registration and retrieval of abstract literal nodes
    """

    def setUp(self):
        class MockType:
            """Custom mock type for testing purposes."""
            pass

        class AnotherMockType:
            """Another custom mock type for testing purposes."""
            pass

        class TemporaryMockTypeNode(IRSchemaNode, pytype=MockType):
            """Temporary node for MockType for testing purposes."""
            def test(self, pytree: Any) -> bool:
                return isinstance(pytree, MockType)

            def validate(self, pytree: Any) -> None:
                if not self.test(pytree):
                    raise PyTreeError(f"Validation failed for {pytree} as MockType")

        class TemporaryAnotherMockTypeNode(IRSchemaNode, pytype=AnotherMockType):
            """Temporary node for AnotherMockType for testing purposes."""
            def test(self, pytree: Any) -> bool:
                return isinstance(pytree, AnotherMockType)

            def validate(self, pytree: Any) -> None:
                if not self.test(pytree):
                    raise PyTreeError(f"Validation failed for {pytree} as AnotherMockType")

        class TemporaryAbstractMockTypeNode(IRSchemaNode, pytype=AbstractType(MockType)):
            """Temporary abstract node for MockType for testing purposes."""
            def test(self, pytree: Any) -> bool:
                return isinstance(pytree, MockType)

            def validate(self, pytree: Any) -> None:
                if not self.test(pytree):
                    raise PyTreeError(f"Validation failed for {pytree} as Abstract MockType")

        class TemporaryAbstractAnotherMockTypeNode(IRSchemaNode, pytype=AbstractType(AnotherMockType)):
            """Temporary abstract node for AnotherMockType for testing purposes."""
            def test(self, pytree: Any) -> bool:
                return isinstance(pytree, AnotherMockType)

            def validate(self, pytree: Any) -> None:
                if not self.test(pytree):
                    raise PyTreeError(f"Validation failed for {pytree} as Abstract AnotherMockType")

        self.MockType = MockType
        self.AnotherMockType = AnotherMockType
        self.temp_nodes = [
            TemporaryMockTypeNode,
            TemporaryAnotherMockTypeNode,
            TemporaryAbstractMockTypeNode,
            TemporaryAbstractAnotherMockTypeNode,
        ]

    def tearDown(self):
        for temp_node in self.temp_nodes:
            IRSchemaNode._node_registry.pop(temp_node.__name__, None)
            IRSchemaNode._abstract_node_registry.pop(temp_node.__name__, None)

    def test_literal_node_registry(self):
        self.assertEqual(IRSchemaNode.from_type(self.MockType()), self.temp_nodes[0])
        self.assertEqual(IRSchemaNode.from_type(self.AnotherMockType()), self.temp_nodes[1])
        with self.assertRaises(PyTreeError):
            IRSchemaNode.from_type(PyTreeError)

    def test_abstract_literal_node_registry(self):
        self.assertEqual(IRSchemaNode.from_type(AbstractType(self.MockType)), self.temp_nodes[2])
        self.assertEqual(IRSchemaNode.from_type(AbstractType(self.AnotherMockType)), self.temp_nodes[3])
        with self.assertRaises(PyTreeError):
            IRSchemaNode.from_type(AbstractType(dict))

    def test_validate_method(self):
        node = IRSchemaNode.from_type(self.MockType())
        self.assertTrue(node().test(self.MockType()))
        node().validate(self.MockType())  # Should not raise an error

        with self.assertRaises(PyTreeError):
            node().validate(self.AnotherMockType())  # Should raise a validation error

class TestLiteralNodes(unittest.TestCase):
    """Unit tests for literal nodes."""

    def test_literal_node_instantiation(self):
        # Ensure that instantiating LiteralNode directly returns the appropriate subclass
        self.assertIsInstance(LiteralNode(5), IntNode)
        self.assertIsInstance(LiteralNode(True), BoolNode)
        self.assertIsInstance(LiteralNode("test"), StrNode)
        self.assertIsInstance(LiteralNode(3.14), FloatNode)

        with self.assertRaises(PyTreeError) as cm:
            LiteralNode(object())
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing direct instantiation of LiteralNode with invalid type:")
            print(f"Validation failed: {cm.exception}")

    def test_int_node(self):
        node = IntNode(5)
        self.assertTrue(node.test(5))
        self.assertFalse(node.test(6))
        with self.assertRaises(PyTreeError):
            IntNode("not an int")
        node.validate(5)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(6)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing IntNode with invalid value:")
            print(f"Validation failed: {cm.exception}")

    def test_bool_node(self):
        node = BoolNode(True)
        self.assertTrue(node.test(True))
        self.assertFalse(node.test(False))
        with self.assertRaises(PyTreeError):
            BoolNode("not a bool")
        node.validate(True)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(False)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing BoolNode with invalid value:")
            print(f"Validation failed: {cm.exception}")

    def test_str_node(self):
        node = StrNode("test")
        self.assertTrue(node.test("test"))
        self.assertFalse(node.test("not test"))
        with self.assertRaises(PyTreeError):
            StrNode(123)
        node.validate("test")
        with self.assertRaises(PyTreeError) as cm:
            node.validate("not test")
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing StrNode with invalid value:")
            print(f"Validation failed: {cm.exception}")

    def test_float_node(self):
        node = FloatNode(3.14)
        self.assertTrue(node.test(3.14))
        self.assertFalse(node.test(2.71))
        with self.assertRaises(PyTreeError):
            FloatNode("not a float")
        node.validate(3.14)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(2.71)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing FloatNode with invalid value:")
            print(f"Validation failed: {cm.exception}")

    def test_registry(self):
        self.assertEqual(IRSchemaNode.from_type(3), IntNode)
        self.assertEqual(IRSchemaNode.from_type(True), BoolNode)
        self.assertEqual(IRSchemaNode.from_type("4"), StrNode)
        self.assertEqual(IRSchemaNode.from_type(4.5), FloatNode)
        with self.assertRaises(PyTreeError):
            IRSchemaNode.from_type(object)

class TestAbstractLiteralNodes(unittest.TestCase):
    """
    Unit tests for abstract literal nodes.
    These tests cover:
    - AbstractIntNode with min and max constraints
    - AbstractBoolNode for boolean values
    - AbstractStrNode for string values
    - AbstractFloatNode with min and max constraints
    """

    def test_abstract_int_node(self):
        node = AbstractIntNode(min_value=0, max_value=10)
        self.assertTrue(node.test(5))
        self.assertFalse(node.test(-1))
        self.assertFalse(node.test(11))
        self.assertFalse(node.test("not an int"))
        node.validate(5)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(-1)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractIntNode with value -1:")
            print(f"Validation failed: {cm.exception}")
        with self.assertRaises(PyTreeError) as cm:
            node.validate(11)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractIntNode with value 11:")
            print(f"Validation failed: {cm.exception}")
        with self.assertRaises(PyTreeError) as cm:
            node.validate("not an int")
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractIntNode with value 'not an int':")
            print(f"Validation failed: {cm.exception}")

    def test_abstract_bool_node(self):
        node = AbstractBoolNode()
        self.assertTrue(node.test(True))
        self.assertTrue(node.test(False))
        self.assertFalse(node.test("not a bool"))
        node.validate(True)
        with self.assertRaises(PyTreeError) as cm:
            node.validate("not a bool")
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractBoolNode with value 'not a bool':")
            print(f"Validation failed: {cm.exception}")

    def test_abstract_str_node(self):
        node = AbstractStrNode()
        self.assertTrue(node.test("test"))
        self.assertFalse(node.test(123))
        node.validate("test")
        with self.assertRaises(PyTreeError) as cm:
            node.validate(123)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractStrNode with value 123:")
            print(f"Validation failed: {cm.exception}")

    def test_abstract_float_node(self):
        node = AbstractFloatNode(min_value=0.0, max_value=10.0)
        self.assertTrue(node.test(5.0))
        self.assertFalse(node.test(-0.1))
        self.assertFalse(node.test(10.1))
        self.assertFalse(node.test("not a float"))
        node.validate(5.0)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(-0.1)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractFloatNode with value -0.1:")
            print(f"Validation failed: {cm.exception}")
        with self.assertRaises(PyTreeError) as cm:
            node.validate(10.1)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractFloatNode with value 10.1:")
            print(f"Validation failed: {cm.exception}")
        with self.assertRaises(PyTreeError) as cm:
            node.validate("not a float")
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractFloatNode with value 'not a float':")
            print(f"Validation failed: {cm.exception}")

    def test_registry(self):
        self.assertEqual(IRSchemaNode.from_type(int), AbstractIntNode)
        self.assertEqual(IRSchemaNode.from_type(bool), AbstractBoolNode)
        self.assertEqual(IRSchemaNode.from_type(str), AbstractStrNode)
        self.assertEqual(IRSchemaNode.from_type(float), AbstractFloatNode)
        with self.assertRaises(PyTreeError):
            IRSchemaNode.from_type(object)

class TestBranchNodes(unittest.TestCase):
    """
    Unit tests for branch nodes.
    These tests cover:
    - DictNode with literal keys and values
    - ListNode with each item being an IRSchemaNode
    """

    def test_branch_node_instantiation(self):
        # Ensure that instantiating BranchNode directly returns the appropriate subclass
        schema_dict = {
            LiteralNode("key1"): AbstractIntNode(min_value=0, max_value=10),
            LiteralNode("key2"): AbstractStrNode()
        }
        schema_list = [AbstractIntNode(min_value=0, max_value=10), AbstractStrNode()]

        self.assertIsInstance(BranchNode(schema_dict), DictNode)
        self.assertIsInstance(BranchNode(schema_list), ListNode)

        with self.assertRaises(PyTreeError) as cm:
            BranchNode(object())
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing direct instantiation of BranchNode with invalid type:")
            print(f"Validation failed: {cm.exception}")

    def test_dict_node(self):
        schema = {
            LiteralNode("key1"): AbstractIntNode(min_value=0, max_value=10),
            LiteralNode("key2"): AbstractStrNode()
        }
        node = DictNode(schema)

        pytree_valid = {
            "key1": 5,
            "key2": "test"
        }
        pytree_invalid = {
            "key1": 15,
            "key2": "test"
        }

        self.assertTrue(node.test(pytree_valid))
        self.assertFalse(node.test(pytree_invalid))

        node.validate(pytree_valid)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(pytree_invalid)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing DictNode with invalid pytree:")
            print(f"Validation failed: {cm.exception}")

    def test_invalid_dict_node(self):
        with self.assertRaises(PyTreeError) as cm:
            DictNode({LiteralNode("key1"): 5})  # Invalid value type
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing invalid DictNode with invalid value type:")
            print(f"Validation failed: {cm.exception}")

        with self.assertRaises(PyTreeError) as cm:
            DictNode({"key1": AbstractIntNode(min_value=0, max_value=10)})  # Invalid key type
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing invalid DictNode with invalid key type:")
            print(f"Validation failed: {cm.exception}")

    def test_list_node(self):
        schema = [AbstractIntNode(min_value=0, max_value=10), AbstractStrNode()]
        node = ListNode(schema)

        pytree_valid = [5, "test"]
        pytree_invalid = [15, "test"]

        self.assertTrue(node.test(pytree_valid))
        self.assertFalse(node.test(pytree_invalid))

        node.validate(pytree_valid)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(pytree_invalid)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing ListNode with invalid pytree:")
            print(f"Validation failed: {cm.exception}")

    def test_invalid_list_node(self):
        with self.assertRaises(PyTreeError) as cm:
            ListNode([5, AbstractStrNode()])  # Invalid item type
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing invalid ListNode with invalid item type:")
            print(f"Validation failed: {cm.exception}")

    def test_registry(self):
        self.assertEqual(IRSchemaNode.from_type({}), DictNode)
        self.assertEqual(IRSchemaNode.from_type([]), ListNode)
        with self.assertRaises(PyTreeError):
            IRSchemaNode.from_type(object)

class TestAbstractBranchNodes(unittest.TestCase):
    """
    Unit tests for abstract branch nodes.
    These tests cover:
    - AbstractDictNode with key and value schema nodes
    - AbstractListNode with a single item schema node
    - UnionNode with a list of IRSchemaNodes
    """

    def test_abstract_dict_node(self):
        key_schema = AbstractStrNode()
        value_schema = AbstractIntNode(min_value=0, max_value=10)
        node = AbstractDictNode(key_schema, value_schema)

        pytree_valid = {"key1": 5, "key2": 10}
        pytree_invalid_key = {1: 5, "key2": 10}
        pytree_invalid_value = {"key1": 15, "key2": 10}

        self.assertTrue(node.test(pytree_valid))
        self.assertFalse(node.test(pytree_invalid_key))
        self.assertFalse(node.test(pytree_invalid_value))

        node.validate(pytree_valid)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(pytree_invalid_key)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractDictNode with invalid key:")
            print(f"Validation failed: {cm.exception}")

        with self.assertRaises(PyTreeError) as cm:
            node.validate(pytree_invalid_value)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractDictNode with invalid value:")
            print(f"Validation failed: {cm.exception}")

    def test_abstract_list_node(self):
        item_schema = AbstractIntNode(min_value=0, max_value=10)
        node = AbstractListNode(item_schema)

        pytree_valid = [5, 7, 10]
        pytree_invalid = [5, 7, 15]

        self.assertTrue(node.test(pytree_valid))
        self.assertFalse(node.test(pytree_invalid))

        node.validate(pytree_valid)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(pytree_invalid)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractListNode with invalid item:")
            print(f"Validation failed: {cm.exception}")

    def test_union_node(self):
        schemas = [AbstractIntNode(min_value=0, max_value=10), AbstractStrNode()]
        node = UnionNode(schemas)

        pytree_valid_int = 5
        pytree_valid_str = "test"
        pytree_invalid = 15

        self.assertTrue(node.test(pytree_valid_int))
        self.assertTrue(node.test(pytree_valid_str))
        self.assertFalse(node.test(pytree_invalid))

        node.validate(pytree_valid_int)
        node.validate(pytree_valid_str)
        with self.assertRaises(PyTreeError) as cm:
            node.validate(pytree_invalid)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing UnionNode with invalid pytree:")
            print(f"Validation failed: {cm.exception}")

    def test_registry(self):
        self.assertEqual(IRSchemaNode.from_type(dict), AbstractDictNode)
        self.assertEqual(IRSchemaNode.from_type(list), AbstractListNode)
        self.assertEqual(IRSchemaNode.from_type(Union), UnionNode)
        with self.assertRaises(PyTreeError):
            IRSchemaNode.from_type(object)
