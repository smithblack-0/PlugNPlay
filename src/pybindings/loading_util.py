import itertools
import typing
from typing import Any, Union, List, Dict, Generator, Callable
from src.pybindings.pytrees import PyTreeError, is_schema_leaf
from src.pybindings.pytrees import FormalSchema, SchemaGroup


def convert_type_to_schema(type_hint: Any) -> Generator[Any, None, None]:
    """
    Convert a type hint to a pytree schema recursively.

    Args:
        type_hint (Any): The type hint to convert.

    Yields:
        Any: The corresponding schema.
    """
    # Handle leaf case
    if is_schema_leaf(type_hint):
        yield type_hint
    elif hasattr(type_hint, "__origin__"):
        # Handle branches
        origin = typing.get_origin(type_hint)
        if Union is origin:
            branches = typing.get_args(type_hint)
            for branch in branches:
                yield from convert_type_to_schema(branch)

        elif list is origin:
            element_generators = [convert_type_to_schema(item) for item in typing.get_args(type_hint)]
            for element_combination in itertools.product(*element_generators):
                yield list(element_combination)

        elif dict is origin:
            key_type, value_type = typing.get_args(type_hint)
            key_schemas = list(convert_type_to_schema(key_type))
            value_schemas = list(convert_type_to_schema(value_type))
            for key_schema, value_schema in itertools.product(key_schemas, value_schemas):
                yield {key_schema : value_schema}

    else:
        raise PyTreeError(f"Unsupported type hint: {type_hint}")



def extract_schemagroup_from_function(func: Callable, name: str, priority: int = 0) -> SchemaGroup:
    """
    Extract type hints from a function and convert them into a SchemaGroup.

    Args:
        func (Callable): The function to extract type hints from.
        name (str): The name of the schema group.
        priority (int): The priority of the schema group.

    Returns:
        SchemaGroup: The corresponding SchemaGroup.
    """
    type_hints = typing.get_type_hints(func)

    parameter_schemas = {}
    for param, hint in type_hints.items():
        if param == 'return':
            continue
        parameter_schemas[param] = list(convert_type_to_schema(hint))

    return_schema = list(convert_type_to_schema(type_hints.get('return', Any)))

    schema_dict = {
        "parameters": parameter_schemas,
        "return": return_schema
    }

    formal_schemas = []
    for param_schema in schema_dict["parameters"].values():
        for ret_schema in schema_dict["return"]:
            formal_schema = {"parameters": param_schema, "return": ret_schema}
            formal_schemas.append(FormalSchema(formal_schema))

    return SchemaGroup(formal_schemas, name, priority)
