"""
A Pytree utility module, this contains types and functions for representing
pytree schemas.

---- What is a pytree? ----

A pytree in and of itself is exactly what it sounds like - a tree formed of python datastructures.
However, for the purpose of this module, pytrees can have only the following leaves and branches

*branches*

- list
- dict: Additionally, only one of the given leaf types can be a key.

* leaves

- int
- float
- str
- bool

---- What is a pytree schema ----

A pytree schema is, simply put, a schema for a pytree. No terrible sophistication is needed for this project to succeed, so we simply are going to assert correct type.

A pytree schema may have additional leaf types:

- Type[int]
- Type[float]
- Type[str]
- Type[bool]


---- what does it mean to satisfy a schema ----

Lets suppose we have a pytree and a pytree schema. What does it mean for the pytree to satisfy
the schema?

- All branches must be the same between them
- When a schema node is an instance, equality must be satisfied between the schema and tree note
- When a schema node is a type, the tree node must be of the schema type
"""


import typing
from typing import Any, Dict, Type, List, Union

class PyTreeError(Exception):
    """Custom exception for pytree errors."""
    pass

class AbstractType:
    """Class representing an abstract type for schema matching."""
    def __init__(self, pytype: Type[Any]):
        self.pytype = pytype

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, AbstractType) and self.pytype is other.pytype

### Node tests ###
# One important factor in pytrees is the intermediate language used to store
# a tree.
#
# This section contains logic underlying it, including registry logic.


class IRSchemaNode:
    """Base class for all IR schema nodes."""
    _node_registry: Dict[Type[Any], Type['IRSchemaNode']] = {}
    _abstract_node_registry: Dict[Type[Any], Type['IRSchemaNode']] = {}

    def __init_subclass__(cls, pytype: Any = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if pytype is not None:
            if isinstance(pytype, type):
                IRSchemaNode._node_registry[pytype] = cls
            elif isinstance(pytype, AbstractType):
                IRSchemaNode._abstract_node_registry[pytype.pytype] = cls
            else:
                raise PyTreeError(f"Unsupported pytype: {pytype}")

    @classmethod
    def from_type(cls, obj: Any | Type[Any]) -> Type['IRSchemaNode']:
        """
        Get the corresponding IRSchemaNode class from the object.

        Args:
            obj (Any): The object to match.

        Returns:
            Type[IRSchemaNode]: The corresponding IRSchemaNode class.
        """
        if type(obj) in cls._node_registry:
            return cls._node_registry[type(obj)]
        elif obj in cls._abstract_node_registry:
            return cls._abstract_node_registry[obj]
        raise PyTreeError(f"No IRSchemaNode registered for object of type: {type(obj)}")

    def test(self, pytree: Any) -> bool:
        """
        Test if the given pytree matches the schema tree. Must be implemented
        by subclasses. Should recursively call test and return false on failure.

        Args:
            pytree (Any): The pytree to test.

        Returns:
            bool: True if the pytree matches the schema tree, otherwise False.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def validate(self, pytree: Any) -> None:
        """
        Validate if the given pytree matches the schema tree. Must be implemented
        by subclasses. Should recursively call validate and raise PyTreeError on failure.

        Args:
            pytree (Any): The pytree to validate.

        Raises:
            PyTreeError: If the pytree does not match the schema tree.
        """
        raise NotImplementedError("Subclasses should implement this method.")

## Literal nodes ##
class LiteralNode(IRSchemaNode):
    """
    A literal node with a specific value.

    This represents a value with a specific type.
    """

    def __new__(cls, value: Any):
        if cls is LiteralNode:
            # Determine the appropriate subclass based on the type of value
            node_cls = IRSchemaNode.from_type(value)
            if node_cls is cls:
                raise PyTreeError(f"Cannot instantiate {cls.__name__} directly. Use specific literal nodes instead.")
            # Create an instance of the appropriate subclass
            instance = super(LiteralNode, node_cls).__new__(node_cls)
            instance.__init__(value)  # Initialize the instance
            return instance
        return super().__new__(cls)

class IntNode(LiteralNode, pytype=int):
    """A literal integer node."""

    def __init__(self, value: int):
        if not isinstance(value, int):
            raise PyTreeError("Value must be an integer.")
        self.value = value

    def test(self, pytree: Any) -> bool:
        return pytree == self.value

    def validate(self, pytree: Any) -> None:
        if not self.test(pytree):
            raise PyTreeError(f"Validation failed: {pytree} does not match the literal integer value {self.value}")

class BoolNode(LiteralNode, pytype=bool):
    """A literal boolean node."""

    def __init__(self, value: bool):
        if not isinstance(value, bool):
            raise PyTreeError("Value must be a boolean.")
        self.value = value

    def test(self, pytree: Any) -> bool:
        return pytree == self.value

    def validate(self, pytree: Any) -> None:
        if not self.test(pytree):
            raise PyTreeError(f"Validation failed: {pytree} does not match the literal boolean value {self.value}")

class StrNode(LiteralNode, pytype=str):
    """A literal string node."""

    def __init__(self, value: str):
        if not isinstance(value, str):
            raise PyTreeError("Value must be a string.")
        self.value = value

    def test(self, pytree: Any) -> bool:
        return pytree == self.value

    def validate(self, pytree: Any) -> None:
        if not self.test(pytree):
            raise PyTreeError(f"Validation failed: {pytree} does not match the literal string value {self.value}")

class FloatNode(LiteralNode, pytype=float):
    """A literal float node."""

    def __init__(self, value: float):
        if not isinstance(value, float):
            raise PyTreeError("Value must be a float.")
        self.value = value

    def test(self, pytree: Any) -> bool:
        return pytree == self.value

    def validate(self, pytree: Any) -> None:
        if not self.test(pytree):
            raise PyTreeError(f"Validation failed: {pytree} does not match the literal float value {self.value}")

### Abstract literal nodes ###
from typing import Any, Optional

class AbstractLiteralNode(IRSchemaNode):
    """
    Base class for abstract literal nodes.

    An abstract literal node provides a type and possible other features that must match,
    but does not bind a literal to an exact instance.
    """

class AbstractIntNode(AbstractLiteralNode, pytype=AbstractType(int)):
    """An abstract integer node with optional min and max values."""

    def __init__(self, min_value: Optional[int] = None, max_value: Optional[int] = None):
        self.min_value = min_value
        self.max_value = max_value

    def test(self, pytree: Any) -> bool:
        if not isinstance(pytree, int):
            return False
        if self.min_value is not None and pytree < self.min_value:
            return False
        if self.max_value is not None and pytree > self.max_value:
            return False
        return True

    def validate(self, pytree: Any) -> None:
        if not isinstance(pytree, int):
            raise PyTreeError(f"Validation failed: {pytree} is not an integer")
        if self.min_value is not None and pytree < self.min_value:
            raise PyTreeError(f"Validation failed: {pytree} is less than minimum value {self.min_value}")
        if self.max_value is not None and pytree > self.max_value:
            raise PyTreeError(f"Validation failed: {pytree} is greater than maximum value {self.max_value}")

class AbstractBoolNode(AbstractLiteralNode, pytype=AbstractType(bool)):
    """An abstract boolean node."""

    def test(self, pytree: Any) -> bool:
        return isinstance(pytree, bool)

    def validate(self, pytree: Any) -> None:
        if not isinstance(pytree, bool):
            raise PyTreeError(f"Validation failed: {pytree} is not a boolean")

class AbstractStrNode(AbstractLiteralNode, pytype=AbstractType(str)):
    """An abstract string node."""

    def test(self, pytree: Any) -> bool:
        return isinstance(pytree, str)

    def validate(self, pytree: Any) -> None:
        if not isinstance(pytree, str):
            raise PyTreeError(f"Validation failed: {pytree} is not a string")

class AbstractFloatNode(AbstractLiteralNode, pytype=AbstractType(float)):
    """An abstract float node with optional min and max values."""

    def __init__(self, min_value: Optional[float] = None, max_value: Optional[float] = None):
        self.min_value = min_value
        self.max_value = max_value

    def test(self, pytree: Any) -> bool:
        if not isinstance(pytree, float):
            return False
        if self.min_value is not None and pytree < self.min_value:
            return False
        if self.max_value is not None and pytree > self.max_value:
            return False
        return True

    def validate(self, pytree: Any) -> None:
        if not isinstance(pytree, float):
            raise PyTreeError(f"Validation failed: {pytree} is not a float")
        if self.min_value is not None and pytree < self.min_value:
            raise PyTreeError(f"Validation failed: {pytree} is less than minimum value {self.min_value}")
        if self.max_value is not None and pytree > self.max_value:
            raise PyTreeError(f"Validation failed: {pytree} is greater than maximum value {self.max_value}")

## Branch Nodes ##
class BranchNode(IRSchemaNode):
    """
    Base class for branch nodes.

    A branch node contains ordered data structures with fixed keys or entries
    in a particular order. This includes dictionaries with fixed keys and lists
    with a specific sequence of elements.
    """

    def __new__(cls, schema: Any):
        if cls is BranchNode:
            # Determine the appropriate subclass based on the type of schema
            node_cls = IRSchemaNode.from_type(schema)
            if node_cls is cls:
                raise PyTreeError(f"Cannot instantiate {cls.__name__} directly. Use specific branch nodes instead.")
            # Create an instance of the appropriate subclass
            instance = super(BranchNode, node_cls).__new__(node_cls)
            instance.__init__(schema)  # Initialize the instance
            return instance
        return super().__new__(cls)

class DictNode(BranchNode, pytype=dict):
    """A dictionary node with defined literal keys and values."""

    def __init__(self, schema: Dict[LiteralNode, IRSchemaNode]):
        for key, value in schema.items():
            if not isinstance(key, LiteralNode):
                raise PyTreeError(f"Invalid key type: {type(key)}. Expected LiteralNode.")
            if not isinstance(value, IRSchemaNode):
                raise PyTreeError(f"Invalid value type: {type(value)}. Expected IRSchemaNode.")
        self.schema = schema

    def test(self, pytree: Any) -> bool:
        if not isinstance(pytree, dict):
            return False
        if len(pytree) != len(self.schema):
            return False
        for key_node, value_schema in self.schema.items():
            key = key_node.value
            if key not in pytree:
                return False
            if not value_schema.test(pytree[key]):
                return False
        return True

    def validate(self, pytree: Any) -> None:
        if not isinstance(pytree, dict):
            raise PyTreeError(f"Validation failed: {pytree} is not a dictionary")
        if len(pytree) != len(self.schema):
            raise PyTreeError(f"Validation failed: {pytree} does not match the schema size {len(self.schema)}")
        for key_node, value_schema in self.schema.items():
            key = key_node.value
            if key not in pytree:
                raise PyTreeError(f"Validation failed: key {key} not found in the pytree")
            try:
                value_schema.validate(pytree[key])
            except PyTreeError as e:
                raise PyTreeError(f"Validation failed for key {key}: {e}")

class ListNode(BranchNode, pytype=list):
    """A list node with each item in the list being an IRSchemaNode."""

    def __init__(self, schema: List[IRSchemaNode]):
        if not all(isinstance(item, IRSchemaNode) for item in schema):
            raise PyTreeError("All items in the schema list must be IRSchemaNode instances.")
        self.schema = schema

    def test(self, pytree: Any) -> bool:
        if not isinstance(pytree, list):
            return False
        if len(pytree) != len(self.schema):
            return False
        for item, schema_item in zip(pytree, self.schema):
            if not schema_item.test(item):
                return False
        return True

    def validate(self, pytree: Any) -> None:
        if not isinstance(pytree, list):
            raise PyTreeError(f"Validation failed: {pytree} is not a list")
        if len(pytree) != len(self.schema):
            raise PyTreeError(f"Validation failed: {pytree} does not match the schema size {len(self.schema)}")
        for i, (item, schema_item) in enumerate(zip(pytree, self.schema)):
            try:
                schema_item.validate(item)
            except PyTreeError as e:
                raise PyTreeError(f"Validation failed for item at index {i}: {e}")

### Abstract branch nodes ###

class AbstractBranchNode(IRSchemaNode):
    """
    Base class for abstract branch nodes.
    """

class AbstractDictNode(AbstractBranchNode, pytype=AbstractType(dict)):
    """An abstract dictionary node with key and value schema nodes."""

    def __init__(self, key_schema: IRSchemaNode, value_schema: IRSchemaNode):
        if not isinstance(key_schema, IRSchemaNode):
            raise PyTreeError("Key schema must be an IRSchemaNode instance.")
        if not isinstance(value_schema, IRSchemaNode):
            raise PyTreeError("Value schema must be an IRSchemaNode instance.")
        self.key_schema = key_schema
        self.value_schema = value_schema

    def test(self, pytree: Any) -> bool:
        if not isinstance(pytree, dict):
            return False
        for key, value in pytree.items():
            if not self.key_schema.test(key):
                return False
            if not self.value_schema.test(value):
                return False
        return True

    def validate(self, pytree: Any) -> None:
        if not isinstance(pytree, dict):
            raise PyTreeError(f"Validation failed: {pytree} is not a dictionary")
        for key, value in pytree.items():
            try:
                self.key_schema.validate(key)
            except PyTreeError as e:
                raise PyTreeError(f"Validation failed for key {key}: {e}")
            try:
                self.value_schema.validate(value)
            except PyTreeError as e:
                raise PyTreeError(f"Validation failed for value {value}: {e}")

class AbstractListNode(AbstractBranchNode, pytype=AbstractType(list)):
    """An abstract list node with a single item schema node."""

    def __init__(self, item_schema: IRSchemaNode):
        if not isinstance(item_schema, IRSchemaNode):
            raise PyTreeError("Item schema must be an IRSchemaNode instance.")
        self.item_schema = item_schema

    def test(self, pytree: Any) -> bool:
        if not isinstance(pytree, list):
            return False
        for item in pytree:
            if not self.item_schema.test(item):
                return False
        return True

    def validate(self, pytree: Any) -> None:
        if not isinstance(pytree, list):
            raise PyTreeError(f"Validation failed: {pytree} is not a list")
        for i, item in enumerate(pytree):
            try:
                self.item_schema.validate(item)
            except PyTreeError as e:
                raise PyTreeError(f"Validation failed for item at index {i}: {e}")

class UnionNode(AbstractBranchNode, pytype=AbstractType(Union)):
    """A union node that accepts a list of IRSchemaNodes."""

    def __init__(self, schemas: List[IRSchemaNode]):
        if not all(isinstance(schema, IRSchemaNode) for schema in schemas):
            raise PyTreeError("All items in the schemas list must be IRSchemaNode instances.")
        self.schemas = schemas

    def test(self, pytree: Any) -> bool:
        return any(schema.test(pytree) for schema in self.schemas)

    def validate(self, pytree: Any) -> None:
        for schema in self.schemas:
            try:
                schema.validate(pytree)
                return
            except PyTreeError:
                continue
        raise PyTreeError(f"Validation failed: {pytree} does not match any schema in the union")
