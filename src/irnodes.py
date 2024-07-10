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
from typing import Any, Dict, Type, List, Union, Callable, Optional, get_origin, get_type_hints, get_args

# Define a recursive type alias for PyTrees with specific leaf types
Leaf = Union[str, bool, float, int]
PyTree = Union[Leaf, List['PyTree'], Dict[str, 'PyTree']]

# Define some basic issues
class IRNodeError(Exception):
    """Custom exception for IR errors."""
    pass

class AbstractType:
    """
    Class representing an abstract type for schema matching.

    This is used solely as a kind of flag to distinguish
    between, for example, AbstractType(int) and int
    """
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
                raise IRNodeError(f"Unsupported pytype: {pytype}")


    @classmethod
    def literal_from_node(cls, obj: Type['IRSchemaNode']) -> Type[Any]:
        reverse_map = {v: k for k, v in cls._node_registry.items()}
        return reverse_map[obj]

    @classmethod
    def abstract_from_node(cls, obj: Type['IRSchemaNode']) -> Type[Any]:
        reverse_map = {v: k for k, v in cls._abstract_node_registry.items()}
        return reverse_map[obj]

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
        raise IRNodeError(f"No IRSchemaNode registered for object of type: {type(obj)}")

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

    def intersect(self, other: 'IRSchemaNode') -> 'IRSchemaNode':
        """
        Finds an intersection between this tree and another.

        This means walking the two trees and keeping the most specific
        node.

        :param other: The other tree to walk
        :return: The merged tree
        :raises: PyTreeError if something goes wrong.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def intersect_like(self, other: 'IRSchemaNode') -> 'IRSchemaNode':
        """
        Intersect two nodes of the same type. Default behavior is to return the current node.

        :param other: The other node to intersect with
        :return: The intersected node
        """
        return self

## Literal nodes ##
class LiteralNode(IRSchemaNode):
    """
    A literal node with a specific value.

    This represents a value with a specific type.
    """

    value: Any

    def __new__(cls, value: Any):
        if cls is LiteralNode:
            # Determine the appropriate subclass based on the type of value
            node_cls = IRSchemaNode.from_type(value)
            if node_cls is cls:
                raise IRNodeError(f"Cannot instantiate {cls.__name__} directly. Use specific literal nodes instead.")
            # Create an instance of the appropriate subclass
            instance = super(LiteralNode, node_cls).__new__(node_cls)
            instance.value = value  # Set the value attribute
            return instance
        return super().__new__(cls)

    def __init__(self, value: Any):
        self.value = value
        self.pytype = type(value)

    def test(self, pytree: Any) -> bool:
        """
        Test if the given pytree matches the literal value.

        Args:
            pytree (Any): The pytree to test.

        Returns:
            bool: True if the pytree matches the literal value, otherwise False.
        """
        if not isinstance(pytree, self.pytype):
            return False
        return pytree == self.value

    def validate(self, pytree: Any) -> None:
        """
        Validate if the given pytree matches the literal value.

        Args:
            pytree (Any): The pytree to validate.

        Raises:
            PyTreeError: If the pytree does not match the literal value.
        """
        if not isinstance(pytree,self.pytype):
            raise IRNodeError(f"Validation failed: '{pytree}' does not have type '{type(self.value)}'")
        if pytree != self.value:
            raise IRNodeError(f"Validation failed: {pytree} does not match {self.value}")

    def intersect(self, other: 'IRSchemaNode') -> 'IRSchemaNode':
        """Return the intersection with another schema node."""
        type_of_self = type(self)
        abstract_node = IRSchemaNode.from_type(self.pytype)
        print(isinstance(other, abstract_node))
        if isinstance(other, AbstractAnyNode) or isinstance(other, IRSchemaNode.from_type(self.pytype)):
            return self
        if isinstance(other, type_of_self):
            if self.value == other.value:
                return self
            else:
                raise IRNodeError(f"Cannot perform intersection: {self.value} and {other.value} are different")
        raise IRNodeError(f"Cannot perform intersection with incompatible node: {type(other)}")

    def __eq__(self, other):
        return hash(self) == hash(other)
    def __hash__(self):
        return hash(hash(self.value) + hash(self.pytype))
class IntNode(LiteralNode, pytype=int):
    """A literal integer node."""
    def __init__(self, value: int):
        if not isinstance(value, int):
            raise IRNodeError("Value must be an integer.")
        super().__init__(value)

class BoolNode(LiteralNode, pytype=bool):
    """A literal boolean node."""

    def __init__(self, value: bool):
        if not isinstance(value, bool):
            raise IRNodeError("Value must be a boolean.")
        super().__init__(value)
class StrNode(LiteralNode, pytype=str):
    """A literal string node."""

    def __init__(self, value: str):
        if not isinstance(value, str):
            raise IRNodeError("Value must be a string.")
        super().__init__(value)

class FloatNode(LiteralNode, pytype=float):
    """A literal float node."""
    def __init__(self, value: float):
        if not isinstance(value, float):
            raise IRNodeError("Value must be a float.")
        super().__init__(value)

### Abstract literal nodes ###
class AbstractLiteralNode(IRSchemaNode):
    """
    Base class for abstract literal nodes.

    An abstract literal node provides a type and possible other features that must match,
    but does not bind a literal to an exact instance.
    """
    pytype: Type[Any]
    def __init__(self, pytype: Type[Any]):
        self.pytype = pytype

    def test(self, pytree: Any) -> bool:
        """
        Test if the given pytree matches the abstract literal node.

        Args:
            pytree (Any): The pytree to test.

        Returns:
            bool: True if the pytree matches the abstract literal node, otherwise False.
        """
        if not isinstance(pytree, self.pytype):
            return False
        return self.check_special_cases(pytree) is None

    def validate(self, pytree: Any) -> None:
        """
        Validate if the given pytree matches the abstract literal node.

        Args:
            pytree (Any): The pytree to validate.

        Raises:
            PyTreeError: If the pytree does not match the abstract literal node.
        """
        if not isinstance(pytree, self.pytype):
            raise IRNodeError(f"Validation failed: {pytree} is not of type {self.pytype}")
        special_case_error = self.check_special_cases(pytree)
        if special_case_error:
            raise IRNodeError(f"Validation failed: {special_case_error}")

    def intersect(self, other: 'IRSchemaNode') -> 'IRSchemaNode':
        """Return the intersection with another schema node."""
        if isinstance(other, AbstractAnyNode):
            return self
        if isinstance(other, type(self)):
            return self.intersect_like(other)
        raise IRNodeError(f"Cannot perform intersection with incompatible node: {type(other)}")

    def check_special_cases(self, pytree: Any) -> Optional[str]:
        """
        Check for special cases to enforce additional constraints.
        Derived classes can override this method to add their specific logic.

        Args:
            pytree (Any): The pytree to check.

        Returns:
            Optional[str]: An error message if a special constraint is violated, None otherwise.
        """
        return None
    def hash_special_cases(self)->int:
        """ Implement to account for special restrictions."""
        return 0
    def __eq__(self, other):
        return hash(self) == hash(other)
    def __hash__(self):
        return hash(self.hash_special_cases() + hash(self.pytype))


class AbstractIntNode(AbstractLiteralNode, pytype=AbstractType(int)):
    """An abstract integer node with optional min and max values."""

    def __init__(self, min_value: Optional[int] = None, max_value: Optional[int] = None):
        super().__init__(int)
        self.min_value = min_value
        self.max_value = max_value

    def hash_special_cases(self) ->int:
        return hash(hash(self.min_value) + hash(self.max_value))
    def check_special_cases(self, pytree: Any) -> Optional[str]:
        if self.min_value is not None and pytree < self.min_value:
            return f"{pytree} is less than minimum value {self.min_value}"
        if self.max_value is not None and pytree > self.max_value:
            return f"{pytree} is greater than maximum value {self.max_value}"
        return None

    def intersect_like(self, other: 'AbstractIntNode') -> 'AbstractIntNode':
        if self.min_value is not None and other.min_value is not None and self.min_value != other.min_value:
            raise IRNodeError(f"Cannot intersect: conflicting min values {self.min_value} and {other.min_value}")
        if self.max_value is not None and other.max_value is not None and self.max_value != other.max_value:
            raise IRNodeError(f"Cannot intersect: conflicting max values {self.max_value} and {other.max_value}")

        min_value = self.min_value if self.min_value is not None else other.min_value
        max_value = self.max_value if self.max_value is not None else other.max_value
        return AbstractIntNode(min_value=min_value, max_value=max_value)

class AbstractBoolNode(AbstractLiteralNode, pytype=AbstractType(bool)):
    """An abstract boolean node."""

    def __init__(self):
        super().__init__(bool)

class AbstractStrNode(AbstractLiteralNode, pytype=AbstractType(str)):
    """An abstract string node."""

    def __init__(self):
        super().__init__(str)


class AbstractFloatNode(AbstractLiteralNode, pytype=AbstractType(float)):
    """An abstract float node with optional min and max values."""

    def __init__(self, min_value: Optional[float] = None, max_value: Optional[float] = None):
        super().__init__(float)
        self.min_value = min_value
        self.max_value = max_value

    def check_special_cases(self, pytree: Any) -> Optional[str]:
        if self.min_value is not None and pytree < self.min_value:
            return f"{pytree} is less than minimum value {self.min_value}"
        if self.max_value is not None and pytree > self.max_value:
            return f"{pytree} is greater than maximum value {self.max_value}"
        return None

    def intersect_like(self, other: 'AbstractFloatNode') -> 'AbstractFloatNode':
        if self.min_value is not None and other.min_value is not None and self.min_value != other.min_value:
            raise IRNodeError(f"Cannot intersect: conflicting min values {self.min_value} and {other.min_value}")
        if self.max_value is not None and other.max_value is not None and self.max_value != other.max_value:
            raise IRNodeError(f"Cannot intersect: conflicting max values {self.max_value} and {other.max_value}")

        min_value = self.min_value if self.min_value is not None else other.min_value
        max_value = self.max_value if self.max_value is not None else other.max_value
        return AbstractFloatNode(min_value=min_value, max_value=max_value)

    def hash_special_cases(self) ->int:
        return hash(hash(self.min_value) + hash(self.max_value))
class AbstractAnyNode(AbstractLiteralNode, pytype=AbstractType(Any)):
    """An abstract node that accepts any value."""

    def __init__(self):
        super().__init__(Any)

    def test(self, pytree: Any) -> bool:
        return True

    def validate(self, pytree: Any) -> None:
        pass

    def intersect(self, other: 'IRSchemaNode') -> 'IRSchemaNode':
        return self if isinstance(other, AbstractAnyNode) else other

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
                raise IRNodeError(f"Cannot instantiate {cls.__name__} directly. Use specific branch nodes instead.")
            # Create an instance of the appropriate subclass
            instance = super(BranchNode, node_cls).__new__(node_cls)
            instance.__init__(schema)  # Initialize the instance
            return instance
        return super().__new__(cls)

    def __init__(self, pytype: Type[Any]):
        self.pytype = pytype
    def intersect(self, other: 'IRSchemaNode') -> 'IRSchemaNode':
        """Return the intersection with another schema node."""
        if isinstance(other, AbstractAnyNode):
            return self
        if isinstance(other, type(self)):
            return self.intersect_like(other)
        if isinstance(other, AbstractBranchNode) and other.pytype == self.pytype:
            return self
        raise IRNodeError(f"Cannot perform intersection with incompatible node: {type(other)}")

    def intersect_like(self, other: 'BranchNode') -> 'BranchNode':
        """Intersection logic specific to the branch node."""
        raise NotImplementedError("Subclasses should implement this method.")

class DictNode(BranchNode, pytype=dict):
    """A dictionary node with defined literal keys and values."""

    def __init__(self, schema: Dict[LiteralNode, IRSchemaNode]):
        for key, value in schema.items():
            if not isinstance(key, LiteralNode):
                raise IRNodeError(f"Invalid key type: {type(key)}. Expected LiteralNode.")
            if not isinstance(value, IRSchemaNode):
                raise IRNodeError(f"Invalid value type: {type(value)}. Expected IRSchemaNode.")
        self.schema = schema
        super().__init__(dict)

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
            raise IRNodeError(f"Validation failed: {pytree} is not a dictionary")
        if len(pytree) != len(self.schema):
            raise IRNodeError(f"Validation failed: {pytree} does not match the schema size {len(self.schema)}")
        for key_node, value_schema in self.schema.items():
            key = key_node.value
            if key not in pytree:
                raise IRNodeError(f"Validation failed: key {key} not found in the pytree")
            try:
                value_schema.validate(pytree[key])
            except IRNodeError as e:
                raise IRNodeError(f"Validation failed for key {key}: {e}")

    def intersect_like(self, other: 'DictNode') -> 'DictNode':
        if list(self.schema.keys()) != list(other.schema.keys()):
            raise IRNodeError("Cannot perform intersection: Dictionary keys do not match")

        new_schema = {}
        for key, value in self.schema.items():
            new_schema[key] = value.intersect(other.schema[key])
        return DictNode(new_schema)

class ListNode(BranchNode, pytype=list):
    """A list node with each item in the list being an IRSchemaNode."""

    def __init__(self, schema: List[IRSchemaNode]):
        if not all(isinstance(item, IRSchemaNode) for item in schema):
            raise IRNodeError("All items in the schema list must be IRSchemaNode instances.")
        self.schema = schema
        super().__init__(list)

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
            raise IRNodeError(f"Validation failed: {pytree} is not a list")
        if len(pytree) != len(self.schema):
            raise IRNodeError(f"Validation failed: {pytree} does not match the schema size {len(self.schema)}")
        for i, (item, schema_item) in enumerate(zip(pytree, self.schema)):
            try:
                schema_item.validate(item)
            except IRNodeError as e:
                raise IRNodeError(f"Validation failed for item at index {i}: {e}")

    def intersect_like(self, other: 'ListNode') -> 'ListNode':
        if len(self.schema) != len(other.schema):
            raise IRNodeError("Cannot perform intersection: List lengths do not match")

        new_schema = []
        for item1, item2 in zip(self.schema, other.schema):
            new_schema.append(item1.intersect(item2))
        return ListNode(new_schema)

### Abstract branch nodes ###

class AbstractBranchNode(IRSchemaNode):
    """
    Base class for abstract branch nodes.
    """
    def __init__(self, pytype: Type[Any]):
        self.pytype = pytype
    def intersect(self, other: 'IRSchemaNode') -> 'IRSchemaNode':
        """Return the intersection with another schema node."""
        if isinstance(other, AbstractAnyNode):
            return self
        if isinstance(other, type(self)):
            return self.intersect_like(other)
        if isinstance(other, BranchNode) and other.pytype == self.pytype:
            return other
        raise IRNodeError(f"Cannot perform intersection with incompatible node: {type(other)}")

    def intersect_like(self, other: 'AbstractBranchNode') -> 'AbstractBranchNode':
        """Intersection logic specific to the branch node."""
        raise NotImplementedError("Subclasses should implement this method.")
class AbstractDictNode(AbstractBranchNode, pytype=AbstractType(dict)):
    """An abstract dictionary node with key and value schema nodes."""

    def __init__(self, key_schema: IRSchemaNode, value_schema: IRSchemaNode):
        if not isinstance(key_schema, IRSchemaNode):
            raise IRNodeError("Key schema must be an IRSchemaNode instance.")
        if not isinstance(value_schema, IRSchemaNode):
            raise IRNodeError("Value schema must be an IRSchemaNode instance.")
        self.key_schema = key_schema
        self.value_schema = value_schema
        super().__init__(dict)
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
            raise IRNodeError(f"Validation failed: {pytree} is not a dictionary")
        for key, value in pytree.items():
            try:
                self.key_schema.validate(key)
            except IRNodeError as e:
                raise IRNodeError(f"Validation failed for key {key}: {e}")
            try:
                self.value_schema.validate(value)
            except IRNodeError as e:
                raise IRNodeError(f"Validation failed for value {value}: {e}")
    def intersect_like(self, other: 'AbstractDictNode') -> 'AbstractDictNode':
        key_schema = self.key_schema.intersect(other.key_schema)
        value_schema = self.value_schema.intersect(other.value_schema)
        return AbstractDictNode(key_schema, value_schema)


class AbstractListNode(AbstractBranchNode, pytype=AbstractType(list)):
    """An abstract list node with a single item schema node."""

    def __init__(self, item_schema: IRSchemaNode):
        if not isinstance(item_schema, IRSchemaNode):
            raise IRNodeError("Item schema must be an IRSchemaNode instance.")
        self.item_schema = item_schema
        super().__init__(list)

    def test(self, pytree: Any) -> bool:
        if not isinstance(pytree, list):
            return False
        for item in pytree:
            if not self.item_schema.test(item):
                return False
        return True

    def validate(self, pytree: Any) -> None:
        if not isinstance(pytree, list):
            raise IRNodeError(f"Validation failed: {pytree} is not a list")
        for i, item in enumerate(pytree):
            try:
                self.item_schema.validate(item)
            except IRNodeError as e:
                raise IRNodeError(f"Validation failed for item at index {i}: {e}")

    def intersect_like(self, other: 'AbstractListNode') -> 'AbstractListNode':
        return AbstractListNode(self.item_schema.intersect(other.item_schema))

class UnionNode(AbstractBranchNode, pytype=AbstractType(Union)):
    """A union node that accepts a list of IRSchemaNodes."""

    def __init__(self, schemas: List[IRSchemaNode]):
        if not all(isinstance(schema, IRSchemaNode) for schema in schemas):
            raise IRNodeError("All items in the schemas list must be IRSchemaNode instances.")
        self.schemas = schemas
        super().__init__(Union)
    def test(self, pytree: Any) -> bool:
        return any(schema.test(pytree) for schema in self.schemas)

    def validate(self, pytree: Any) -> None:
        for schema in self.schemas:
            try:
                schema.validate(pytree)
                return
            except IRNodeError:
                continue
        raise IRNodeError(f"Validation failed: {pytree} does not match any schema in the union")

    def intersect_like(self, other: 'UnionNode') -> 'UnionNode':
        outcome = [selfitem.schema.intersect(other.schema) for selfitem,other
                   in zip(self.schema, other.schema)]
        return UnionNode(outcome)


def type_hint_to_schema(type_hint: Any) -> IRSchemaNode:
    """
    Convert a Python type hint to an IRSchema tree.

    Args:
        type_hint (Any): The type hint to convert.

    Returns:
        IRSchemaNode: The corresponding IRSchema tree.
    """
    origin = get_origin(type_hint)
    args = get_args(type_hint)

    if origin is Union:
        # Handle Union types
        schemas = [type_hint_to_schema(arg) for arg in args]
        return UnionNode(schemas)

    elif origin is list:
        # Handle List types
        item_schema = type_hint_to_schema(args[0])
        return AbstractListNode(item_schema)

    elif origin is dict:
        # Handle Dict types
        key_schema = type_hint_to_schema(args[0])
        value_schema = type_hint_to_schema(args[1])
        return AbstractDictNode(key_schema, value_schema)

    else:
        # Handle Literal types
        node_class = IRSchemaNode.from_type(type_hint)
        return node_class()


def pytree_to_schema(pytree: Any) -> IRSchemaNode:
    """
    Convert a pytree to an IRSchema tree.

    Args:
        pytree (Any): The pytree to convert.

    Returns:
        IRSchemaNode: The corresponding IRSchema tree.
    """
    if isinstance(pytree, list):
        # Handle List types
        item_schemas = [pytree_to_schema(item) for item in pytree]
        return ListNode(item_schemas)

    elif isinstance(pytree, dict):
        # Handle Dict types
        key_schemas = {LiteralNode(key): pytree_to_schema(value) for key, value in pytree.items()}
        return DictNode(key_schemas)

    else:
        # Handle Literal types
        node_cls = IRSchemaNode.from_type(pytree)
        return node_cls(pytree)

