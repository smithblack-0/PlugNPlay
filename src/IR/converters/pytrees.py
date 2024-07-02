"""

Converts a pytree directly into the IR format.

Pytrees converted this way are never schema, but
instead consist of actual values for all leaves and branches

"""

import textwrap
from ..exceptions import ImportException, ExportException
from .. import nodes
from typing import Any


# Get the conversion maps
literals_type_map = nodes.Literal.get_type_map()
trees_type_map = nodes.DataNode.get_type_map()

literals_node_map = { v : k for k, v in literals_type_map.items()}
trees_node_map = {v : k for k, v in trees_type_map.items()}

def map_type_to_node(item: Any)->nodes.SchemaNode:
    """
    Converts an item into a IR node if possible.
    """

    item_type = type(item)

    # Convert literals
    if item_type in literals_type_map:
        literal_class = literals_type_map[item_type]
        return literal_class(item)

    # Convert tree elements
    if item_type in trees_type_map:
        trees_class = trees_type_map[item_type]
        return trees_class(item)

    # Item not found. Throw an error
    msg = f"""
    An issue occurred while importing a pytree. 
    The available types were:
    
    {literals_type_map.keys()}
    {trees_type_map.keys()}
    
    However, the object of type {item_type} was not among these.
    """
    msg = textwrap.dedent(msg)
    raise ImportException(msg)

def map_node_to_type(node: nodes.SchemaNode)->Any:
    """
    Maps a node back to its pytree type format.

    If this is possible...

    :param node: The node
    :return: The instanced type, if possible...
    """
    node_type = type(node)

    def create_exception(name: str):


    # Remap literals
    if node_type in literals_node_map:
        node: nodes.Literal
        if node.value is None:
            msg = f"""
                 Issue exporting a IR schema to a pytree.

                 Attempt was made to export a pytree that contained
                 abstract elements. The node {name} should
                 have contained a value, but instead was an abstract
                 schema entity.
                 """
            msg = textwrap.dedent(msg)
            return ExportException(msg)

    # Remap trees
    if node_type in trees_node_map:
        node: nodes.DataNode
        return node.children

    if node_type in