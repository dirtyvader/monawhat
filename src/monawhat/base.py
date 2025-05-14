"""Module implementing a base monad class that all other monads can extend."""

from typing import TypeVar, Generic, Any
from collections.abc import Callable

from monawhat.identity import Identity

M = TypeVar("M", bound="BaseMonad[Any]")  # Monad type (for return type of bind/map)
A = TypeVar("A")  # Input type
B = TypeVar("B")  # Output type


class BaseMonad(Generic[A]):
    """Base class for all monads.

    This class provides common functionality for monads and serves as a
    foundation for implementing specific monads. It uses the Identity monad
    internally for pure values.

    Subclasses must implement _bind_implementation and _map_implementation.
    """

    def map(self, f: Callable[[A], B]) -> "BaseMonad[B]":
        """Apply a function to the value(s) inside the monad.

        Args:
            f: The function to apply to the value(s).

        Returns:
            A new monad with the transformed value(s).
        """
        return self._map_implementation(f)

    def bind(self, f: Callable[[A], Any]) -> Any:
        """Chain this monad with a function that returns another monad.

        Args:
            f: A function that takes the value(s) of this monad and returns a new monad.

        Returns:
            The new monad returned by the function.
        """
        return self._bind_implementation(f)

    def _map_implementation(self, f: Callable[[A], B]) -> "BaseMonad[B]":
        """Implementation of the map operation for this specific monad.

        Subclasses must override this method to provide monad-specific behavior.

        Args:
            f: The function to apply to the value(s).

        Returns:
            A new monad with the transformed value(s).
        """
        raise NotImplementedError("Subclasses must implement this")

    def _bind_implementation(self, f: Callable[[A], Any]) -> Any:
        """Implementation of the bind operation for this specific monad.

        Subclasses must override this method to provide monad-specific behavior.

        Args:
            f: A function that takes the value(s) of this monad and returns a new monad.

        Returns:
            The new monad returned by the function.
        """
        raise NotImplementedError("Subclasses must implement this")

    @classmethod
    def pure(cls, value: A, *args: Any, **kwargs: Any) -> "BaseMonad[A]":
        """Create a monad containing a pure value.

        This uses the Identity monad internally to represent pure values.
        Subclasses should override this to provide monad-specific implementation.

        Args:
            value: The value to wrap in the monad.
            *args: Additional positional arguments for specific monad implementations.
            **kwargs: Additional keyword arguments for specific monad implementations.

        Returns:
            A monad containing the value.
        """
        return cls._pure_implementation(Identity(value).get(), *args, **kwargs)

    @classmethod
    def _pure_implementation(cls, value: A, *args: Any, **kwargs: Any) -> "BaseMonad[A]":
        """Implementation of the pure operation for this specific monad.

        Subclasses must override this method to provide monad-specific behavior.

        Args:
            value: The value to wrap in the monad.
            *args: Additional positional arguments for specific monad implementations.
            **kwargs: Additional keyword arguments for specific monad implementations.

        Returns:
            A monad containing the value.
        """
        raise NotImplementedError("Subclasses must implement this")
