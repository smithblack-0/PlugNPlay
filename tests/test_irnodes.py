import unittest
from typing import Any, List, Dict, Union
from src.irnodes import IntNode, BoolNode, StrNode, FloatNode, AbstractType
from src.irnodes import AbstractBoolNode, AbstractFloatNode
from src.irnodes import BranchNode, DictNode, ListNode, AbstractAnyNode, IRNodeError
from src.irnodes import LiteralNode, AbstractIntNode, AbstractStrNode, AbstractDictNode, AbstractListNode, UnionNode, IRSchemaNode
from src.irnodes import type_hint_to_schema, pytree_to_schema

SHOW_ERROR_MESSAGES = True

### Node tests ###
# One important factor in pytrees is the intermediate language used to store
# a tree.
#
# This section contains tests for it.

class TestIRSchemaNode(unittest.TestCase):
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
                    raise IRNodeError(f"Validation failed for {pytree} as MockType")

        class TemporaryAnotherMockTypeNode(IRSchemaNode, pytype=AnotherMockType):
            """Temporary node for AnotherMockType for testing purposes."""
            def test(self, pytree: Any) -> bool:
                return isinstance(pytree, AnotherMockType)

            def validate(self, pytree: Any) -> None:
                if not self.test(pytree):
                    raise IRNodeError(f"Validation failed for {pytree} as AnotherMockType")

        class TemporaryAbstractMockTypeNode(IRSchemaNode, pytype=AbstractType(MockType)):
            """Temporary abstract node for MockType for testing purposes."""
            def test(self, pytree: Any) -> bool:
                return isinstance(pytree, MockType)

            def validate(self, pytree: Any) -> None:
                if not self.test(pytree):
                    raise IRNodeError(f"Validation failed for {pytree} as Abstract MockType")

        class TemporaryAbstractAnotherMockTypeNode(IRSchemaNode, pytype=AbstractType(AnotherMockType)):
            """Temporary abstract node for AnotherMockType for testing purposes."""
            def test(self, pytree: Any) -> bool:
                return isinstance(pytree, AnotherMockType)

            def validate(self, pytree: Any) -> None:
                if not self.test(pytree):
                    raise IRNodeError(f"Validation failed for {pytree} as Abstract AnotherMockType")

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
        with self.assertRaises(IRNodeError):
            IRSchemaNode.from_type(IRNodeError)

    def test_abstract_literal_node_registry(self):
        self.assertEqual(IRSchemaNode.from_type(self.MockType), self.temp_nodes[2])
        self.assertEqual(IRSchemaNode.from_type(self.AnotherMockType), self.temp_nodes[3])
        with self.assertRaises(IRNodeError):
            IRSchemaNode.from_type(object)

    def test_validate_method(self):
        node = IRSchemaNode.from_type(self.MockType())
        self.assertTrue(node().test(self.MockType()))
        node().validate(self.MockType())  # Should not raise an error

        with self.assertRaises(IRNodeError):
            node().validate(self.AnotherMockType())  # Should raise a validation error
class TestLiteralNodes(unittest.TestCase):
    """Unit tests for literal nodes."""

    def test_literal_node_instantiation(self):
        # Ensure that instantiating LiteralNode directly returns the appropriate subclass
        self.assertIsInstance(LiteralNode(5), IntNode)
        self.assertIsInstance(LiteralNode(True), BoolNode)
        self.assertIsInstance(LiteralNode("test"), StrNode)
        self.assertIsInstance(LiteralNode(3.14), FloatNode)

        with self.assertRaises(IRNodeError) as cm:
            LiteralNode(object())
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing direct instantiation of LiteralNode with invalid type:")
            print(f"Validation failed: {cm.exception}")

    def test_int_node(self):
        node = IntNode(5)
        self.assertTrue(node.test(5))
        self.assertFalse(node.test(6))
        with self.assertRaises(IRNodeError):
            IntNode("not an int")
        node.validate(5)
        with self.assertRaises(IRNodeError) as cm:
            node.validate(6)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing IntNode with invalid value:")
            print(f"Validation failed: {cm.exception}")

    def test_bool_node(self):
        node = BoolNode(True)
        self.assertTrue(node.test(True))
        self.assertFalse(node.test(False))
        with self.assertRaises(IRNodeError):
            BoolNode("not a bool")
        node.validate(True)
        with self.assertRaises(IRNodeError) as cm:
            node.validate(False)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing BoolNode with invalid value:")
            print(f"Validation failed: {cm.exception}")

    def test_str_node(self):
        node = StrNode("test")
        self.assertTrue(node.test("test"))
        self.assertFalse(node.test("not test"))
        with self.assertRaises(IRNodeError):
            StrNode(123)
        node.validate("test")
        with self.assertRaises(IRNodeError) as cm:
            node.validate("not test")
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing StrNode with invalid value:")
            print(f"Validation failed: {cm.exception}")

    def test_float_node(self):
        node = FloatNode(3.14)
        self.assertTrue(node.test(3.14))
        self.assertFalse(node.test(2.71))
        with self.assertRaises(IRNodeError):
            FloatNode("not a float")
        node.validate(3.14)
        with self.assertRaises(IRNodeError) as cm:
            node.validate(2.71)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing FloatNode with invalid value:")
            print(f"Validation failed: {cm.exception}")

    def test_intersect(self):
        int_node = IntNode(5)
        abstract_int_node = AbstractIntNode()
        any_node = AbstractAnyNode()

        # Intersection with AbstractAnyNode
        self.assertEqual(int_node.intersect(any_node), int_node)

        # Intersection with AbstractIntNode
        self.assertEqual(int_node.intersect(abstract_int_node), int_node)

        # Intersection with the same literal node
        self.assertEqual(int_node.intersect(IntNode(5)), int_node)

        # Intersection with a different literal node
        with self.assertRaises(IRNodeError) as cm:
            int_node.intersect(IntNode(6))
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing IntNode intersection with different literal value:")
            print(f"Validation failed: {cm.exception}")

    def test_registry(self):
        self.assertEqual(IRSchemaNode.from_type(3), IntNode)
        self.assertEqual(IRSchemaNode.from_type(True), BoolNode)
        self.assertEqual(IRSchemaNode.from_type("4"), StrNode)
        self.assertEqual(IRSchemaNode.from_type(4.5), FloatNode)
        with self.assertRaises(IRNodeError):
            IRSchemaNode.from_type(object)

class TestAbstractLiteralNodes(unittest.TestCase):
    """
    Unit tests for abstract literal nodes.
    These tests cover:
    - Initialization of all abstract literal nodes
    - Validation logic using AbstractStrNode
    - Test logic using AbstractStrNode
    - Intersect logic using AbstractStrNode
    - Detailed tests for AbstractIntNode and AbstractFloatNode
    - Tests for AbstractAnyNode
    - Registry tests for node registration
    """

    def test_nodes_initialize(self):
        """Test that all node types initialize properly."""
        try:
            AbstractIntNode()
            AbstractBoolNode()
            AbstractStrNode()
            AbstractFloatNode()
            AbstractAnyNode()
        except IRNodeError as e:
            self.fail(f"Initialization failed with error: {e}")

    def test_simple_validate_logic(self):
        """Test that the validate logic is working properly using AbstractStrNode."""
        node = AbstractStrNode()
        node.validate("test")
        with self.assertRaises(IRNodeError) as cm:
            node.validate(123)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractStrNode validate logic:")
            print(f"Validation failed: {cm.exception}")

    def test_simple_test_logic(self):
        """Test that the test logic is working properly using AbstractStrNode."""
        node = AbstractStrNode()
        self.assertTrue(node.test("test"))
        self.assertFalse(node.test(123))

    def test_simple_intersect_logic(self):
        """Test that the intersect logic is working properly using AbstractStrNode."""
        node1 = AbstractStrNode()
        node2 = AbstractStrNode()
        self.assertEqual(node1.intersect(node2), node1)
        with self.assertRaises(IRNodeError) as cm:
            node1.intersect(AbstractIntNode())
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractStrNode intersect logic:")
            print(f"Validation failed: {cm.exception}")

    def test_abstract_int_node(self):
        """Detailed tests for AbstractIntNode including min and max constraints."""
        node = AbstractIntNode(min_value=0, max_value=10)
        self.assertTrue(node.test(5))
        self.assertFalse(node.test(-1))
        self.assertFalse(node.test(11))
        node.validate(5)
        with self.assertRaises(IRNodeError) as cm:
            node.validate(-1)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractIntNode with value -1:")
            print(f"Validation failed: {cm.exception}")
        with self.assertRaises(IRNodeError) as cm:
            node.validate(11)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractIntNode with value 11:")
            print(f"Validation failed: {cm.exception}")

        # Test intersect with min and max values
        node1 = AbstractIntNode(min_value=0, max_value=10)
        node2 = AbstractIntNode(min_value=0, max_value=None)
        node3 = AbstractIntNode(min_value=5, max_value=15)
        intersected_node = node1.intersect_like(node2)
        self.assertEqual(intersected_node.min_value, 0)
        self.assertEqual(intersected_node.max_value, 10)
        with self.assertRaises(IRNodeError) as cm:
            node1.intersect_like(node3)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing intersect logic for AbstractIntNode with conflicting min and max values:")
            print(f"Validation failed: {cm.exception}")

    def test_abstract_float_node(self):
        """Detailed tests for AbstractFloatNode including min and max constraints."""
        node = AbstractFloatNode(min_value=0.0, max_value=10.0)
        self.assertTrue(node.test(5.0))
        self.assertFalse(node.test(-0.1))
        self.assertFalse(node.test(10.1))
        node.validate(5.0)
        with self.assertRaises(IRNodeError) as cm:
            node.validate(-0.1)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractFloatNode with value -0.1:")
            print(f"Validation failed: {cm.exception}")
        with self.assertRaises(IRNodeError) as cm:
            node.validate(10.1)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractFloatNode with value 10.1:")
            print(f"Validation failed: {cm.exception}")

        # Test intersect with min and max values
        node1 = AbstractFloatNode(min_value=0.0, max_value=10.0)
        node2 = AbstractFloatNode(min_value=0.0, max_value=None)
        node3 = AbstractFloatNode(min_value=5.0, max_value=15.0)
        intersected_node = node1.intersect_like(node2)
        self.assertEqual(intersected_node.min_value, 0.0)
        self.assertEqual(intersected_node.max_value, 10.0)
        with self.assertRaises(IRNodeError) as cm:
            node1.intersect_like(node3)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing intersect logic for AbstractFloatNode with conflicting min and max values:")
            print(f"Validation failed: {cm.exception}")

    def test_abstract_any_node(self):
        """Tests for AbstractAnyNode."""
        node = AbstractAnyNode()
        self.assertTrue(node.test(123))
        self.assertTrue(node.test("string"))
        self.assertTrue(node.test(True))
        self.assertTrue(node.test(None))

        node.validate(123)
        node.validate("string")
        node.validate(True)
        node.validate(None)

        node_int = IRSchemaNode.from_type(int)()
        node_str = IRSchemaNode.from_type(str)()

        self.assertEqual(node.intersect(node_int), node_int)
        self.assertEqual(node.intersect(node_str), node_str)
        self.assertEqual(node.intersect(node), node)

    def test_registry(self):
        """Test that the nodes are correctly registered."""
        self.assertEqual(IRSchemaNode.from_type(int), AbstractIntNode)
        self.assertEqual(IRSchemaNode.from_type(bool), AbstractBoolNode)
        self.assertEqual(IRSchemaNode.from_type(str), AbstractStrNode)
        self.assertEqual(IRSchemaNode.from_type(float), AbstractFloatNode)
        self.assertEqual(IRSchemaNode.from_type(Any), AbstractAnyNode)
        with self.assertRaises(IRNodeError):
            IRSchemaNode.from_type(object)


class TestBranchNodes(unittest.TestCase):
    """
    Unit tests for branch nodes.
    These tests cover:
    - DictNode with literal keys and values
    - ListNode with each item being an IRSchemaNode
    - Intersection logic for DictNode and ListNode
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

        with self.assertRaises(IRNodeError) as cm:
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
        with self.assertRaises(IRNodeError) as cm:
            node.validate(pytree_invalid)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing DictNode with invalid pytree:")
            print(f"Validation failed: {cm.exception}")

    def test_invalid_dict_node(self):
        with self.assertRaises(IRNodeError) as cm:
            DictNode({LiteralNode("key1"): 5})  # Invalid value type
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing invalid DictNode with invalid value type:")
            print(f"Validation failed: {cm.exception}")

        with self.assertRaises(IRNodeError) as cm:
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
        with self.assertRaises(IRNodeError) as cm:
            node.validate(pytree_invalid)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing ListNode with invalid pytree:")
            print(f"Validation failed: {cm.exception}")

    def test_invalid_list_node(self):
        with self.assertRaises(IRNodeError) as cm:
            ListNode([5, AbstractStrNode()])  # Invalid item type
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing invalid ListNode with invalid item type:")
            print(f"Validation failed: {cm.exception}")

    def test_dict_node_intersection(self):
        schema1 = {
            LiteralNode("key1"): AbstractIntNode(max_value=10),
            LiteralNode("key2"): AbstractStrNode()
        }
        schema2 = {
            LiteralNode("key1"): AbstractIntNode(min_value=0),
            LiteralNode("key2"): AbstractStrNode()
        }
        node1 = DictNode(schema1)
        node2 = DictNode(schema2)

        intersected_node = node1.intersect(node2)
        self.assertIsInstance(intersected_node, DictNode)
        self.assertTrue(intersected_node.schema[LiteralNode("key1")].min_value == 0)
        self.assertTrue(intersected_node.schema[LiteralNode("key1")].max_value == 10)

        schema3 = {
            LiteralNode("key3"): AbstractIntNode(min_value=0, max_value=10)
        }
        node3 = DictNode(schema3)

        with self.assertRaises(IRNodeError) as cm:
            node1.intersect(node3)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing DictNode intersection with mismatched keys:")
            print(f"Validation failed: {cm.exception}")

    def test_list_node_intersection(self):
        schema1 = [AbstractIntNode(min_value=0, max_value=None), AbstractStrNode()]
        schema2 = [AbstractIntNode(min_value=None, max_value=15), AbstractStrNode()]
        node1 = ListNode(schema1)
        node2 = ListNode(schema2)

        intersected_node = node1.intersect(node2)
        self.assertIsInstance(intersected_node, ListNode)
        self.assertTrue(intersected_node.schema[0].min_value == 0)
        self.assertTrue(intersected_node.schema[0].max_value == 15)

        schema3 = [AbstractIntNode(min_value=0, max_value=10)]
        node3 = ListNode(schema3)

        with self.assertRaises(IRNodeError) as cm:
            node1.intersect(node3)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing ListNode intersection with mismatched lengths:")
            print(f"Validation failed: {cm.exception}")

    def test_registry(self):
        self.assertEqual(IRSchemaNode.from_type({}), DictNode)
        self.assertEqual(IRSchemaNode.from_type([]), ListNode)
        with self.assertRaises(IRNodeError):
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
        with self.assertRaises(IRNodeError) as cm:
            node.validate(pytree_invalid_key)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing AbstractDictNode with invalid key:")
            print(f"Validation failed: {cm.exception}")

        with self.assertRaises(IRNodeError) as cm:
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
        with self.assertRaises(IRNodeError) as cm:
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
        with self.assertRaises(IRNodeError) as cm:
            node.validate(pytree_invalid)
        if SHOW_ERROR_MESSAGES:
            print("Message generated while testing UnionNode with invalid pytree:")
            print(f"Validation failed: {cm.exception}")

    def test_registry(self):
        self.assertEqual(IRSchemaNode.from_type(dict), AbstractDictNode)
        self.assertEqual(IRSchemaNode.from_type(list), AbstractListNode)
        self.assertEqual(IRSchemaNode.from_type(Union), UnionNode)
        with self.assertRaises(IRNodeError):
            IRSchemaNode.from_type(object)


class TestTypeHintToSchema(unittest.TestCase):
    """
    Unit tests for the type_hint_to_schema function.
    These tests cover:
    - Union types
    - List types
    - Dict types
    - Literal types
    """

    def test_union_type(self):
        type_hint = Union[int, str]
        schema = type_hint_to_schema(type_hint)
        self.assertIsInstance(schema, UnionNode)
        self.assertEqual(len(schema.schemas), 2)
        self.assertIsInstance(schema.schemas[0], AbstractIntNode)
        self.assertIsInstance(schema.schemas[1], AbstractStrNode)

    def test_list_type(self):
        type_hint = List[int]
        schema = type_hint_to_schema(type_hint)
        self.assertIsInstance(schema, AbstractListNode)
        self.assertIsInstance(schema.item_schema, AbstractIntNode)

    def test_dict_type(self):
        type_hint = Dict[str, int]
        schema = type_hint_to_schema(type_hint)
        self.assertIsInstance(schema, AbstractDictNode)
        self.assertIsInstance(schema.key_schema, AbstractStrNode)
        self.assertIsInstance(schema.value_schema, AbstractIntNode)

    def test_literal_type(self):
        type_hint = int
        schema = type_hint_to_schema(type_hint)
        self.assertIsInstance(schema, AbstractIntNode)

class TestPyTreeToSchema(unittest.TestCase):
    """
    Unit tests for the pytree_to_schema function.
    These tests cover:
    - List types
    - Dict types
    - Literal types
    """

    def test_list_type(self):
        pytree = [5, "test", 10.5]
        schema = pytree_to_schema(pytree)
        self.assertIsInstance(schema, ListNode)
        self.assertEqual(len(schema.schema), 3)
        self.assertIsInstance(schema.schema[0], IntNode)
        self.assertIsInstance(schema.schema[1], StrNode)
        self.assertIsInstance(schema.schema[2], FloatNode)

    def test_dict_type(self):
        pytree = {"key1": 5, "key2": 10}
        schema = pytree_to_schema(pytree)
        self.assertIsInstance(schema, DictNode)
        self.assertEqual(len(schema.schema), 2)
        self.assertIsInstance(schema.schema[LiteralNode("key1")], IntNode)
        self.assertIsInstance(schema.schema[LiteralNode("key2")], IntNode)

    def test_literal_type(self):
        pytree = 5
        schema = pytree_to_schema(pytree)
        self.assertIsInstance(schema, IntNode)

    def test_mixed_list(self):
        pytree = [5, "test", 10.5]
        schema = pytree_to_schema(pytree)
        self.assertIsInstance(schema, ListNode)
        self.assertEqual(len(schema.schema), 3)
        self.assertIsInstance(schema.schema[0], IntNode)
        self.assertIsInstance(schema.schema[1], StrNode)
        self.assertIsInstance(schema.schema[2], FloatNode)
    def test_mixed_dict_values(self):
        pytree = {"key1": 5, "key2": "test"}
        schema = pytree_to_schema(pytree)
        self.assertIsInstance(schema, DictNode)
        self.assertEqual(len(schema.schema), 2)
        self.assertIsInstance(schema.schema[LiteralNode("key1")], IntNode)
        self.assertIsInstance(schema.schema[LiteralNode("key2")], StrNode)

    def test_nested_pytree(self):
        pytree = {"key1": [5, "test"], "key2": {"nested_key": 10.5}}
        schema = pytree_to_schema(pytree)
        self.assertIsInstance(schema, DictNode)
        self.assertIsInstance(schema.schema[LiteralNode("key1")], ListNode)
        self.assertIsInstance(schema.schema[LiteralNode("key2")], DictNode)
        self.assertIsInstance(schema.schema[LiteralNode("key1")].schema[0], IntNode)
        self.assertIsInstance(schema.schema[LiteralNode("key1")].schema[1], StrNode)
        self.assertIsInstance(schema.schema[LiteralNode("key2")].schema[LiteralNode("nested_key")], FloatNode)

    def test_registry(self):
        self.assertEqual(IRSchemaNode.from_type({}), DictNode)
        self.assertEqual(IRSchemaNode.from_type([]), ListNode)
        self.assertEqual(IRSchemaNode.from_type(Union), UnionNode)
        with self.assertRaises(IRNodeError):
            IRSchemaNode.from_type(object)
