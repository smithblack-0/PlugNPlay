"""
Registry information is stored here
"""

from typing import TypeVar, Generic, Callable, Type, Dict, Iterator

RegistryObject = TypeVar('RegistryObject')
class Registry(Generic[RegistryObject]):
    def __init__(self):
        self._registry: Dict[str, RegistryObject] = {}

    def register(self, name: str = None) -> Callable[[RegistryObject], RegistryObject]:
        """Decorator for registering a function or class with an optional name."""
        def decorator(obj: RegistryObject) -> RegistryObject:
            key = name if name else obj.__name__
            if key in self._registry:
                raise KeyError(f"Key '{key}' already exists in the registry.")
            self._registry[key] = obj
            return obj
        return decorator

    def deregister(self, name: str) -> None:
        """Remove an item from the registry by name."""
        if name in self._registry:
            del self._registry[name]
        else:
            raise KeyError(f"Key '{name}' not found in the registry.")

    def get(self, name: str) -> RegistryObject:
        """Retrieve an item from the registry by name."""
        return self._registry.get(name, None)

    def list_items(self) -> list:
        """List all registered items."""
        return list(self._registry.keys())

    def __contains__(self, name: str) -> bool:
        """Check if an item exists in the registry."""
        return name in self._registry

    def __len__(self) -> int:
        """Get the number of items in the registry."""
        return len(self._registry)

    def __iter__(self) -> Iterator:
        """Iterate over the registry items."""
        return iter(self._registry.items())

    def __repr__(self) -> str:
        return f"Registry({self._registry})"
    