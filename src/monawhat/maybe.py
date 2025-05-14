"""Module implementing the Option monad for handling optional values.

Examples:
    Create a Just value:

    >>> maybe_value = Maybe.just(42)
    >>> maybe_value.get()
    42

    Create a Nothing value:

    >>> empty = Maybe.nothing()
    >>> empty.is_nothing()
    True

    Map over a Maybe:

    >>> maybe_value = Maybe.just(42)
    >>> doubled = maybe_value.map(lambda x: x * 2)
    >>> doubled.get()
    84

    Handle None values:

    >>> value = Maybe.from_optional(None)
    >>> value.get_or_else(0)
    0

    Chain computations:
    
    >>> def divide(x: int, y: int) -> Maybe[float]:
    ...     return Maybe.just(x / y) if y != 0 else Maybe.nothing()
    >>> result = Maybe.just(10).bind(lambda x: divide(x, 2))
    >>> result.get()
    5.0
"""
from typing import TypeVar
from collections.abc import Callable

from monawhat.base import BaseMonad
from monawhat.either import Either

A = TypeVar("A")  # Input type
B = TypeVar("B")  # Output type
E = TypeVar("E")  # Error type


class Maybe(BaseMonad[A]):
    """Base class for the Option monad. This class should not be instantiated directly.

    Option represents a value that may or may not be present.
    An instance of Option is either a Just (containing a value) or a Nothing.
    """

    def is_just(self) -> bool:
        """Check if this Option is a Just."""
        raise NotImplementedError("Subclasses must implement this")

    def is_nothing(self) -> bool:
        """Check if this Option is a Nothing."""
        raise NotImplementedError("Subclasses must implement this")

    def get_or_else(self, default: A) -> A:
        """Return the value if this is a Just, or the default value if it's a Nothing."""
        raise NotImplementedError("Subclasses must implement this")

    def get(self) -> A:
        """Return the contained value if Just, or raise an error if Nothing."""
        raise NotImplementedError("Subclasses must implement this")

    def to_either(self, error: E) -> "Either[E, A]":
        """Convert this Maybe to an Either.

        Args:
        error: The error value to use if this is Nothing

        Returns:
        Either.left(error) if this is Nothing, otherwise Either.right(self.get())
        """
        if self.is_nothing():
            return Either.left(error)
        return Either.right(self.get())

    @classmethod
    def _pure_implementation(cls, value: A) -> "Just[A]":
        """Implementation of the pure operation for the Maybe monad."""
        return Just(value)

    @staticmethod
    def just(value: A) -> "Just[A]":
        """Create a Just instance containing the given value."""
        return Maybe._pure_implementation(value)

    @staticmethod
    def nothing() -> "Nothing[A]":
        """Create a Nothing instance."""
        return Nothing()

    @staticmethod
    def from_optional(value: A | None) -> "Maybe[A]":
        """Create a Maybe from an optional value.

        Args:
            value: Value that might be None

        Returns:
            Just(value) if value is not None, otherwise Nothing()
        """
        return Maybe.just(value) if value is not None else Maybe.nothing()


class Just(Maybe[A]):
    """The Just case of the Option monad, representing a present value."""

    def __init__(self, value: A) -> None:
        """Initialize a Just instance with a value.

        Args:
            value: The value to store in the Just instance.
        """
        self._value: A = value

    def is_just(self) -> bool:
        """Check if this Option is a Just."""
        return True

    def is_nothing(self) -> bool:
        """Check if this Option is a Nothing."""
        return False

    def _map_implementation(self, f: Callable[[A], B]) -> "Maybe[B]":
        """Apply function f to the contained value and wrap the result in a new Just."""
        return Just(f(self._value))

    def _bind_implementation(self, f: Callable[[A], "Maybe[B]"]) -> "Maybe[B]":
        """Apply function f that returns an Option monad to the contained value and return that monad directly."""
        return f(self._value)

    def get_or_else(self, default: A) -> A:
        """Return the contained value."""
        return self._value

    def get(self) -> A:
        """Return the contained value."""
        return self._value

    def __repr__(self) -> str:
        """Return a string representation of the Just instance."""
        return f"Just({self._value})"


class Nothing(Maybe[A]):
    """The Nothing case of the Option monad, representing the absence of a value."""

    def is_just(self) -> bool:
        """Check if this Option is a Just."""
        return False

    def is_nothing(self) -> bool:
        """Check if this Option is a Nothing."""
        return True

    def _map_implementation(self, f: Callable[[A], B]) -> "Maybe[B]":
        """Nothing values ignore mapping operations."""
        return Nothing()

    def _bind_implementation(self, f: Callable[[A], "Maybe[B]"]) -> "Maybe[B]":
        """Nothing values ignore bind operations."""
        return Nothing()

    def get_or_else(self, default: A) -> A:
        """Return the default value."""
        return default

    def get(self) -> A:
        """Raise an error since Nothing contains no value."""
        raise ValueError("Cannot get value from Nothing")

    def __repr__(self) -> str:
        """Return a string representation of the Nothing instance."""
        return "Nothing()"
