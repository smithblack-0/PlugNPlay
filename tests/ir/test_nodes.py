import unittest
from src.IR.nodes import IntNode, StringNode, BoolNode, FloatNode, Literal, DictNode, ListNode, DataStructureNode, AnyOfNode, VirtualNode

class TestSchemaNodes(unittest.TestCase):

    def test_literal_node_initialization(self):
        int_node = IntNode(42)
        self.assertEqual(int_node.value, 42)

        with self.assertRaises(ValueError):
            IntNode("not an int")

        str_node = StringNode("hello")
        self.assertEqual(str_node.value, "hello")

        with self.assertRaises(ValueError):
            StringNode(123)

        bool_node = BoolNode(True)
        self.assertEqual(bool_node.value, True)

        with self.assertRaises(ValueError):
            BoolNode("not a bool")

        float_node = FloatNode(3.14)
        self.assertEqual(float_node.value, 3.14)

        with self.assertRaises(ValueError):
            FloatNode("not a float")

    def test_datastructure_node_initialization(self):
        children = {"key": IntNode(42)}
        dict_node = DictNode(children)
        self.assertEqual(dict_node.children, children)

        with self.assertRaises(ValueError):
            DictNode(None)

    def test_virtual_node_initialization(self):
        children = [IntNode(42), StringNode("hello")]
        anyof_node = AnyOfNode(children)
        self.assertEqual(anyof_node.children, children)

        with self.assertRaises(ValueError):
            AnyOfNode(None)

    def test_literal_node_attributes(self):
        int_node = IntNode(42)
        self.assertEqual(int_node.__class__.name(), "int")
        self.assertEqual(int_node.__class__.pytype(), int)

    def test_datastructure_node_attributes(self):
        children = {"key": IntNode(42)}
        dict_node = DictNode(children)
        self.assertEqual(dict_node.__class__.name(), "dict")
        self.assertEqual(dict_node.__class__.pytype(), dict)
        self.assertEqual(dict_node.children, children)

    def test_get_literal_node(self):
        int_node = Literal.get_literal_node(42)
        self.assertIsInstance(int_node, IntNode)
        self.assertEqual(int_node.value, 42)

        str_node = Literal.get_literal_node("hello")
        self.assertIsInstance(str_node, StringNode)
        self.assertEqual(str_node.value, "hello")

        float_node = Literal.get_literal_node(3.14)
        self.assertIsInstance(float_node, FloatNode)
        self.assertEqual(float_node.value, 3.14)

    def test_get_literal(self):
        int_node = IntNode(42)
        self.assertEqual(Literal.get_literal(int_node), 42)

        str_node = StringNode("hello")
        self.assertEqual(Literal.get_literal(str_node), "hello")

        float_node = FloatNode(3.14)
        self.assertEqual(Literal.get_literal(float_node), 3.14)

    def test_get_datastructure_node(self):
        children = {"key": IntNode(42)}
        dict_node = DataStructureNode.get_datastructure_node(children)
        self.assertIsInstance(dict_node, DictNode)
        self.assertEqual(dict_node.children, children)

    def test_get_datastructure(self):
        children = {"key": IntNode(42)}
        dict_node = DictNode(children)
        self.assertEqual(DataStructureNode.get_datastructure(dict_node), children)

    def test_default_transform(self):
        int_node = IntNode(42)
        transformed_nodes = list(int_node.default_transform())
        self.assertEqual(len(transformed_nodes), 1)
        self.assertEqual(transformed_nodes[0].value, 42)

    def test_separate_transform(self):
        children = [IntNode(42), StringNode("hello")]
        anyof_node = AnyOfNode(children)
        separated_nodes = list(anyof_node.separate_transform())
        self.assertEqual(len(separated_nodes), 2)
        self.assertIsInstance(separated_nodes[0], IntNode)
        self.assertIsInstance(separated_nodes[1], StringNode)

if __name__ == '__main__':
    unittest.main()
