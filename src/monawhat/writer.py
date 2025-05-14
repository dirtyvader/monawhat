"""Module implementing the Writer monad for accumulating computations with output.

Examples:
    Basic usage with string output:

    >>> w1 = Writer(5, "first ")  # Create a Writer with value 5 and output "first "
    >>> w2 = w1.map(lambda x: x * 2)  # Map value to 10, output unchanged
    >>> w2.run()
    (10, "first ")
    
    Chaining Writers with bind:

    >>> def add_one(x):
    ...     return Writer(x + 1, "added one ")
    >>> w3 = w1.bind(add_one)  # Chain operations, outputs combine
    >>> w3.run()
    (6, "first added one ")
    
    Using tell to add output:

    >>> w4 = Writer.tell("log message ")  # Create Writer with just output
    >>> w4.run()
    (None, "log message ")
    
    Using listen to access output:

    >>> w5 = Writer(42, "answer ").listen()  # Value becomes tuple with output
    >>> w5.run()
    ((42, "answer "), "answer ")
"""

from typing import TypeVar, Generic, cast, Protocol, runtime_checkable, Self
from collections.abc import Callable

from monawhat.base import BaseMonad

A = TypeVar("A")  # Input type
B = TypeVar("B")  # Output type

@runtime_checkable
class Monoid(Protocol):
    """Protocol defining a type that supports the + operator (like a monoid)."""
    def __add__(self, other: Self) -> Self:
        """Combine two monoid values."""
        ...

W = TypeVar("W", bound=Monoid)  # Output accumulation type (monoid)


class Writer(Generic[W, A], BaseMonad[A]):
    """Writer monad for computations that produce a value along with accumulated output.
    
    The Writer monad represents a computation that produces a result along with
    some accumulated output (like a log). It's useful for tracking computations
    that generate additional data alongside their primary result.
    
    The output type W should form a monoid, meaning it has:
    - An associative binary operation for combining values (+ operator)
    - An identity element that, when combined with any value, gives that value back
    
    Common examples: lists, strings, numbers with addition, etc.
    """
    
    def __init__(self, value: A, output: W, combine: Callable[[W, W], W] | None = None) -> None:
        """Initialize a Writer with a value and output.
        
        Args:
            value: The computation result.
            output: The accumulated output.
            combine: Optional function to combine outputs. If None, uses the + operator.
        """
        self._value = value
        self._output = output
        self._combine = combine if combine is not None else (lambda x, y: x + y)
    
    def run(self) -> tuple[A, W]:
        """Extract the value and output from the Writer.
        
        Returns:
            A tuple containing the result value and accumulated output.
        """
        return (self._value, self._output)
    
    def value(self) -> A:
        """Get the value from the Writer.
        
        Returns:
            The result value.
        """
        return self._value
    
    def output(self) -> W:
        """Get the output from the Writer.
        
        Returns:
            The accumulated output.
        """
        return self._output
    
    def _map_implementation(self, f: Callable[[A], B]) -> "Writer[W, B]":
        """Apply a function to the result value while preserving the output.
        
        Args:
            f: The function to apply to the result value.
            
        Returns:
            A new Writer with the transformed value and the same output.
        """
        return Writer(f(self._value), self._output, self._combine)
    
    def _bind_implementation(self, f: Callable[[A], "Writer[W, B]"]) -> "Writer[W, B]":
        """Chain this Writer with a function that returns another Writer.
        
        The outputs from both Writers are combined using the combine function.
        
        Args:
            f: A function that takes the value of this Writer and returns a new Writer.
            
        Returns:
            A new Writer representing the chained computation with combined output.
        """
        new_writer = f(self._value)
        new_value, new_output = new_writer.run()
        
        # Use the combine function to merge outputs
        combined_output = self._combine(self._output, new_output)
        
        return Writer(new_value, combined_output, self._combine)
    
    @classmethod
    def _pure_implementation(cls, value: A) -> "Writer[W, A]":
        """Create a Writer with a value and empty output.
        
        Note: This is just a placeholder; actual Writer.pure implementation needs
        empty and combine values that we don't have here. Use Writer.pure() directly.
        
        Args:
            value: The value to wrap.
            
        Returns:
            Placeholder result - use Writer.pure() directly instead.
        """
        # This is a placeholder - we can't implement pure properly here
        # because we need an empty output of type W and a combine function
        raise NotImplementedError("Use Writer.pure(value, empty, combine) directly instead")
    
    @classmethod
    def pure(cls, value: A, empty: W, combine: Callable[[W, W], W] | None = None) -> "Writer[W, A]":
        """Create a Writer with a value and empty output.
        
        Args:
            value: The value to wrap.
            empty: The identity element for the output monoid.
            combine: Optional function to combine outputs. If None, uses the + operator.
            
        Returns:
            A Writer containing the value and empty output.
        """
        return cls(value, empty, combine)
    
    @classmethod
    def tell(cls, output: W, combine: Callable[[W, W], W] | None = None) -> "Writer[W, None]":
        """Create a Writer that only produces output with no meaningful value.
        
        Args:
            output: The output to produce.
            combine: Optional function to combine outputs. If None, uses the + operator.
            
        Returns:
            A Writer with the given output and None as the value.
        """
        # We need to cast None to type A to satisfy the type checker
        return cast("Writer[W, None]", cls(cast(A, None), output, combine))
    
    def listen(self) -> "Writer[W, tuple[A, W]]":
        """Create a Writer where the value includes the output as well.
        
        Returns:
            A new Writer where the value is paired with the output.
        """
        return Writer((self._value, self._output), self._output, self._combine)
    
    def pass_output(self) -> "Writer[W, A]":
        """Execute this Writer assuming its value is a function that transforms output.
        
        The function in value should have the signature Callable[[W], W].
        
        Returns:
            A Writer where the output is transformed by the function in the value.
        """
        if not callable(self._value):
            raise TypeError("Value must be a function for pass_output")
        
        # Cast the value to the expected callable type
        transform_function = cast(Callable[[W], W], self._value)
        transformed_output = transform_function(self._output)
        
        # Return a new Writer with the same value but transformed output
        return cast("Writer[W, A]", Writer(self._value, transformed_output, self._combine))
    
    def censor(self, f: Callable[[W], W]) -> "Writer[W, A]":
        """Apply a function to the output while preserving the value.
        
        Args:
            f: The function to apply to the output.
            
        Returns:
            A new Writer with the same value and transformed output.
        """
        return Writer(self._value, f(self._output), self._combine)
    
    def __repr__(self) -> str:
        """Return a string representation of the Writer."""
        return f"Writer(value={self._value}, output={self._output})"