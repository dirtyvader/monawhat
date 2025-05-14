"""Module implementing the Either monad for handling success/failure cases.

Examples:
    Basic usage for error handling:
    
    >>> from monawhat.either import Either
    >>> 
    >>> def safe_divide(a, b):
    ...     if b == 0:
    ...         return Either.left(f"Cannot divide {a} by zero")
    ...     return Either.right(a / b)
    >>> 
    >>> # Successful case
    >>> result = safe_divide(10, 2)
    >>> if result.is_right():
    ...     print(f"Result: {result.get()}")  # Output: Result: 5.0
    >>> 
    >>> # Error case
    >>> result = safe_divide(10, 0)
    >>> if result.is_left():
    ...     print(f"Error: {result.get()}")  # Output: Error: Cannot divide 10 by zero
    
    Chaining operations with bind:
    
    >>> def get_user(user_id):
    ...     # Simulate fetching a user from database
    ...     if user_id > 0:
    ...         return Either.right({"id": user_id, "email": "user@example.com"})
    ...     return Either.left(f"User with id {user_id} not found")
    >>> 
    >>> def send_email(user, message):
    ...     # Simulate sending an email
    ...     if "email" in user:
    ...         return Either.right(f"Email sent to {user['email']}")
    ...     return Either.left("Email address not found")
    >>> 
    >>> # Chain operations together
    >>> result = (Either.right(1)
    ...           .bind(get_user)
    ...           .bind(lambda user: send_email(user, "Welcome!")))
    >>> print(result)  # Output: Right(Email sent to user@example.com)
    
    Using pattern matching:
    
    >>> def process_result(result):
    ...     return result.match(
    ...         left_fn=lambda error: f"Operation failed: {error}",
    ...         right_fn=lambda value: f"Operation succeeded with value: {value}"
    ...     )
    >>> 
    >>> success = Either.right(42)
    >>> failure = Either.left("Invalid input")
    >>> 
    >>> print(process_result(success))  # Output: Operation succeeded with value: 42
    >>> print(process_result(failure))  # Output: Operation failed: Invalid input
"""

from typing import TypeVar, Generic, cast
from collections.abc import Callable

from monawhat.base import BaseMonad

A = TypeVar("A")  # Left type (typically error)
B = TypeVar("B")  # Right type (typically success)
C = TypeVar("C")  # Output type for transformations


class Either(Generic[A, B], BaseMonad[B]):
    """Base class for the Either monad. This class should not be instantiated directly.

    Either represents a value of one of two possible types (a disjoint union).
    An instance of Either is either a Left or a Right.
    """

    def is_left(self) -> bool:
        """Check if this Either is a Left."""
        raise NotImplementedError("Subclasses must implement this")

    def is_right(self) -> bool:
        """Check if this Either is a Right."""
        raise NotImplementedError("Subclasses must implement this")

    def get_or_else(self, default: B) -> B:
        """Return the value if this is a Right, or the default value if it's a Left."""
        raise NotImplementedError("Subclasses must implement this")

    def get(self) -> A | B:
        """Return the contained value."""
        raise NotImplementedError("Subclasses must implement this")

    def match(self, left_fn: Callable[[A], C], right_fn: Callable[[B], C]) -> C:
        """Apply the appropriate function based on whether this is a Left or Right.

        Args:
            left_fn: Function to apply if this is a Left
            right_fn: Function to apply if this is a Right

        Returns:
            The result of applying the appropriate function
        """
        if self.is_left():
            return left_fn(cast(A, self.get()))
        else:
            return right_fn(cast(B, self.get()))

    @classmethod
    def _pure_implementation(cls, value: B) -> "Right[A, B]":
        """Implementation of the pure operation for the Either monad."""
        return Right(value)

    @staticmethod
    def left(value: A) -> "Left[A, B]":
        """Create a Left instance containing the given value."""
        return Left(value)

    @staticmethod
    def right(value: B) -> "Right[A, B]":
        """Create a Right instance containing the given value."""
        return Either._pure_implementation(value)


class Left(Either[A, B]):
    """The Left case of the Either monad, typically representing failure."""

    def __init__(self, value: A) -> None:
        """Initialize a Left instance with a value.

        Args:
            value: The value to store in the Left instance.
        """
        self._value: A = value

    def is_left(self) -> bool:
        """Check if this Either is a Left."""
        return True

    def is_right(self) -> bool:
        """Check if this Either is a Right."""
        return False

    def _map_implementation(self, f: Callable[[B], C]) -> "Either[A, C]":
        """Left values ignore mapping operations."""
        return Left(self._value)

    def _bind_implementation(self, f: Callable[[B], "Either[A, C]"]) -> "Either[A, C]":
        """Left values ignore bind operations."""
        return Left(self._value)

    def get_or_else(self, default: B) -> B:
        """Return the default value."""
        return default

    def get(self) -> A:
        """Return the contained value."""
        return self._value

    def __repr__(self) -> str:
        """Return a string representation of the Left instance."""
        return f"Left({self._value})"


class Right(Either[A, B]):
    """The Right case of the Either monad, typically representing success."""

    def __init__(self, value: B) -> None:
        """Initialize a Right instance with a value.

        Args:
            value: The value to store in the Right instance.
        """
        self._value: B = value

    def is_left(self) -> bool:
        """Check if this Either is a Left."""
        return False

    def is_right(self) -> bool:
        """Check if this Either is a Right."""
        return True

    def _map_implementation(self, f: Callable[[B], C]) -> "Either[A, C]":
        """Apply function f to the contained value and wrap the result in a new Right."""
        return Right(f(self._value))

    def _bind_implementation(self, f: Callable[[B], "Either[A, C]"]) -> "Either[A, C]":
        """Apply function f that returns an Either monad to the contained value and return that monad directly."""
        return f(self._value)

    def get_or_else(self, default: B) -> B:
        """Return the contained value."""
        return self._value

    def get(self) -> B:
        """Return the contained value."""
        return self._value

    def __repr__(self) -> str:
        """Return a string representation of the Right instance."""
        return f"Right({self._value})"
