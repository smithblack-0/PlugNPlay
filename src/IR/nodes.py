import textwrap
from typing import Union, List, Dict, Any, Generator, Type, Optional, Tuple, Callable, Set
import itertools
from abc import ABC, abstractmethod
from .exceptions import TransformException

### Raw schema node definitions ####

# Base SchemaNode class
from typing import Union, List, Dict, Any, Generator, Type, Optional, Tuple, Callable, Set
from abc import ABC, abstractmethod

from typing import Union, List, Dict, Any, Generator, Type, Optional, Tuple, Callable, Set
from abc import ABC, abstractmethod

from typing import Union, List, Dict, Any, Generator, Type, Optional, Tuple, Callable, Set
from abc import ABC, abstractmethod

class SchemaNode(ABC):
    """
    Abstract base class for schema nodes.

    Attributes:
        _name (str): The name of the schema node.
        _pytype (Type): The Python type associated with the schema node.
        _transforms_list (Set[str]): A set of registered transform names.
        _transform_registry (Dict[str, Callable]): A dictionary mapping transform names to their corresponding callables.

    Methods:
        name() -> str: Class method to get the name of the schema node.
        pytype() -> Type: Class method to get the Python type of the schema node.
        register_transform(name: str, operand: Callable[['SchemaNode', Any], Generator['SchemaNode', None, None]]): Class method to register a transform.
        walk() -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]: Abstract method to walk through the available nodes.
        default_transform(data: Any) -> Generator['SchemaNode', None, None]: Abstract method to apply the default transform.
        transform(transform_name: str, data: Any) -> Generator['SchemaNode', None, None]: Method to apply a registered transform.
    """

    _name: str
    _pytype: Type
    _transforms_list: Set[str] = set()
    _transform_registry: Dict[str, Callable] = {}

    @classmethod
    def name(cls) -> str:
        if not hasattr(cls, "_name"):
            raise NotImplementedError("Subclass never implemented the class level _name field")
        return cls._name

    @classmethod
    def pytype(cls) -> Type:
        if not hasattr(cls, "_pytype"):
            raise NotImplementedError("Subclass never implemented the class level '_pytype' field")
        return cls._pytype

    @classmethod
    def register_transform(cls, name: str, operand: Callable[['SchemaNode', Any], Generator['SchemaNode', None, None]]):
        if not hasattr(cls, '_transform_registry'):
            raise RuntimeError("Transform registry is not initialized. Ensure the subclass is properly initialized.")
        cls._transforms_list.add(name)
        cls._transform_registry[name] = operand

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._transform_registry = {}

    @abstractmethod
    def walk(self) -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]:
        """
        Walks the available nodes.

        Yields a list of the path to the node, and the node itself.
        """
        pass

    @abstractmethod
    def default_transform(self, data: Any) -> Generator['SchemaNode', None, None]:
        """
        The default transform must be implemented.
        Generally, it will return a new node built by transforming the low level ones.
        """
        pass

    def transform(self, transform_name: str, data: Any) -> Generator['SchemaNode', None, None]:
        """
        The transform node should be implemented by the subclass.
        It should pass back a generator over all the different versions of the node that were produced after transformation.

        :param transform_name: Name of the transform to apply.
        :param data: Data to be used in the transform.
        :return: A generator yielding all trees produced by the transformation.
        """
        operand = self._transform_registry.get(transform_name, self.default_transform)
        yield from operand(self, data)




# Literal Node base class
class Literal(SchemaNode):
    """
    Base class for literal schema nodes.

    Attributes:
        value (Any): The value of the literal node.

    Methods:
        get_literal_node(instance: Any) -> 'Literal': Class method to get a literal node instance based on type or string.
        get_literal(node: 'Literal') -> Any: Class method to get an instance from a literal node.
        default_transform(data: Any) -> Generator['SchemaNode', None, None]: Applies the default transform.
        walk() -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]: Walks the available nodes.
    """

    _type_registry: Dict[Type, 'Literal'] = {}
    _str_registry: Dict[str, 'Literal'] = {}
    value: Any

    @property



    @classmethod
    def get_literal_node(cls, instance: Any) -> 'Literal':
        """
        Returns a literal node instance based on the provided instance's type or string.

        :param instance: The instance to match against the registry.
        :return: An instance of the corresponding Literal subclass.
        """
        instance_type = type(instance)
        node_class = cls._type_registry.get(instance_type)
        if node_class:
            return node_class(instance)
        elif isinstance(instance, str):
            node_class = cls._str_registry.get(instance)
            if node_class:
                return node_class()
        raise ValueError(f"Unsupported instance: {instance}")

    @classmethod
    def get_literal(cls, node: 'Literal') -> Any:
        """
        Returns the instance corresponding to the provided literal node.

        :param node: An instance of a Literal subclass.
        :return: The instance corresponding to the literal node.
        """
        reverse_type_registry = {v: k for k, v in cls._type_registry.items()}
        node_type = type(node)
        instance_type = reverse_type_registry[node_type]
        if node.value is not None:
            return instance_type(node.value)
        return instance_type

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        def transform_to_unbound_schema(self, **directives):
            yield self.__class__()

        def visualize_types(self, **directives):
            yield StringNode(cls.name())

        cls.register_transform("convert_to_unbound_schema", transform_to_unbound_schema)
        cls.register_transform("visualize_types", visualize_types)

        Literal._type_registry[cls.pytype()] = cls
        Literal._str_registry[cls.name()] = cls

    def __init__(self, value: Optional[Any] = None):
        super().__init__()
        self.value = value

    def default_transform(self, **directives) -> Generator['SchemaNode', None, None]:
        """
        Applies the default transform, which generally returns the node itself.
        """
        yield self

    def walk(self) -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]:
        """
        Walks the available nodes.

        Yields a list of the path to the node, and the node itself.
        """
        yield [], self

class IntNode(Literal):
    """
    A schema node representing an integer type.

    An optional integer value can be provided to bind the node to a specific value.
    If the value is not provided, it means any integer value would work.

    Methods:
        __init__(value: int = None): Initializes the node with an optional integer value.
    """
    _name = "int"
    _pytype = int

    def __init__(self, value: int = None):
        if value is not None and not isinstance(value, int):
            raise ValueError("IntNode value must be an int.")
        super().__init__(value)


class StringNode(Literal):
    """
    A schema node representing a string type.

    An optional string value can be provided to bind the node to a specific value.
    If the value is not provided, it means any string value would work.

    Methods:
        __init__(value: str = None): Initializes the node with an optional string value.
    """
    _name = "string"
    _pytype = str

    def __init__(self, value: str = None):
        if value is not None and not isinstance(value, str):
            raise ValueError("StringNode value must be a string.")
        super().__init__(value)


class BoolNode(Literal):
    """
    A schema node representing a boolean type.

    An optional boolean value can be provided to bind the node to a specific value.
    If the value is not provided, it means any boolean value would work.

    Methods:
        __init__(value: bool = None): Initializes the node with an optional boolean value.
    """
    _name = "bool"
    _pytype = bool

    def __init__(self, value: bool = None):
        if value is not None and not isinstance(value, bool):
            raise ValueError("BoolNode value must be a bool.")
        super().__init__(value)


class FloatNode(Literal):
    """
    A schema node representing a float type.

    An optional float value can be provided to bind the node to a specific value.
    If the value is not provided, it means any float value would work.

    Methods:
        __init__(value: float = None): Initializes the node with an optional float value.
    """
    _name = "float"
    _pytype = float

    def __init__(self, value: float = None):
        if value is not None and not isinstance(value, float):
            raise ValueError("FloatNode value must be a float.")
        super().__init__(value)


# Dataclass Node base class
class DataStructureNode(SchemaNode):
    """
    Base class for data structure schema nodes that can have children nodes.

    Attributes:
        children (Any): The children nodes of this data node.

    Methods:
        __init__(children: Any): Initializes the node with children nodes.
        get_datastructure_node(instance: Any) -> 'DataStructureNode': Class method to get a data structure node instance based on type.
        get_datastructure(node: 'DataStructureNode') -> Any: Class method to get the children from a data structure node.
    """

    _type_registry: Dict[Type, 'DataStructureNode'] = {}

    @classmethod
    def get_datastructure_node(cls, instance: Any) -> 'DataStructureNode':
        """
        Returns a data structure node instance based on the provided instance's type.

        :param instance: The instance to match against the registry.
        :return: An instance of the corresponding DataStructureNode subclass.
        """
        instance_type = type(instance)
        node_class = cls._type_registry.get(instance_type)
        if node_class:
            return node_class(instance)
        raise ValueError(f"Unsupported instance: {instance}")

    @classmethod
    def get_datastructure(cls, node: 'DataStructureNode') -> Any:
        """
        Returns the children corresponding to the provided data structure node.

        :param node: An instance of a DataStructureNode subclass.
        :return: The children corresponding to the data structure node.
        """
        return node.children

    def __init__(self, children: Any):
        if children is None:
            raise ValueError(f"{self.__class__.__name__} children cannot be None.")
        super().__init__()
        self.children = children

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        DataStructureNode._type_registry[cls.pytype()] = cls

class DictNode(DataStructureNode):
    """
    A schema node representing a dictionary.

    Methods:
        __init__(children: Dict[Union[Literal, str], SchemaNode]): Initializes the node with dictionary children nodes.
        walk() -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]: Walks the available nodes.
        default_transform(**directives) -> Generator['SchemaNode', None, None]: Applies the default transform.
    """
    _name = "dict"
    _pytype = dict

    def __init__(self, children: Dict[Union[Literal, str], SchemaNode]):
        if not isinstance(children, dict) or not all(isinstance(k, (str, Literal)) for k in children.keys()):
            raise ValueError("All keys in DictNode must be strings or literals and children must be a dict.")
        if not all(isinstance(v, SchemaNode) for v in children.values()):
            raise ValueError("All values in DictNode must be SchemaNode instances.")
        super().__init__(children)

    def walk(self) -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]:
        """
        Walks the available nodes.

        Yields a list of the path to the node, and the node itself.
        """
        for child in self.children.values():
            for path, node in child.walk():
                yield [self] + path, node

    def default_transform(self, **directives) -> Generator['SchemaNode', None, None]:
        """
        Applies the default transform to the node's children.
        """
        values_generators = [child.transform(**directives) for child in self.children.values()]

        for tree_case in itertools.product(*values_generators):
            yield DictNode(dict(zip(self.children.keys(), tree_case)))


class ListNode(DataStructureNode):
    """
    A schema node representing a list.

    Methods:
        __init__(children: List[SchemaNode]): Initializes the node with list children nodes.
        walk() -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]: Walks the available nodes.
        default_transform(**directives) -> Generator['SchemaNode', None, None]: Applies the default transform.
    """
    _name = "list"
    _pytype = list

    def __init__(self, children: List[SchemaNode]):
        if not isinstance(children, list) or not all(isinstance(child, SchemaNode) for child in children):
            raise ValueError("All elements in ListNode must be SchemaNode instances and children must be a list.")
        super().__init__(children)

    def walk(self) -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]:
        """
        Walks the available nodes.

        Yields a list of the path to the node, and the node itself.
        """
        for child in self.children:
            for path, node in child.walk():
                yield [self] + path, node

    def default_transform(self, **directives) -> Generator['SchemaNode', None, None]:
        """
        Applies the default transform to the node's children.
        """
        values_generators = [child.transform(**directives) for child in self.children]

        for tree_case in itertools.product(*values_generators):
            yield ListNode(list(tree_case))

## Utility node. No direct corrolation to pytree datastructures.
class VirtualNode(SchemaNode):
    """
    Base class for virtual schema nodes that don't have a direct Python equivalency but provide important data.

    Attributes:
        children (Any): The children nodes of this virtual node.

    Methods:
        __init__(children: Any): Initializes the node with children nodes.
    """

    def __init__(self, children: Any):
        if children is None or not isinstance(children, (list, dict, SchemaNode)):
            raise ValueError(f"{self.__class__.__name__} children must be a SchemaNode, list, or dict of SchemaNodes.")
        super().__init__()
        self.children = children


class AnyOfNode(VirtualNode):
    """
    A virtual schema node representing a choice between multiple schemas.

    Methods:
        __init__(children: List[SchemaNode]): Initializes the node with list children nodes.
        walk() -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]: Walks the available nodes.
        default_transform(**directives) -> Generator['SchemaNode', None, None]: Applies the default transform.
        separate_transform(**directives) -> Generator[SchemaNode, None, None]: Splits the node into its children, yielding each child as a separate tree.
    """
    _name = "AnyOf"
    _pytype = None

    def __init__(self, children: List[SchemaNode]):
        if not isinstance(children, list) or not all(isinstance(child, SchemaNode) for child in children):
            raise ValueError("All elements in AnyOfNode must be SchemaNode instances and children must be a list.")
        super().__init__(children)
        self.register_transform("SplitTreesOnOptions", self.separate_transform)

    def walk(self) -> Generator[Tuple[List['SchemaNode'], 'SchemaNode'], None, None]:
        """
        Walks the available nodes.

        Yields a list of the path to the node, and the node itself.
        """
        for child in self.children:
            for path, node in child.walk():
                yield [self] + path, node

    def default_transform(self, **directives) -> Generator['SchemaNode', None, None]:
        """
        Applies the default transform to the node's children.
        """
        values_generators = [child.transform(**directives) for child in self.children]

        for tree_case in itertools.product(*values_generators):
            yield AnyOfNode(list(tree_case))

    def separate_transform(self, **directives) -> Generator[SchemaNode, None, None]:
        """
        Splits the node into its children, yielding each child as a separate tree.
        """
        for child in self.children:
            yield child
