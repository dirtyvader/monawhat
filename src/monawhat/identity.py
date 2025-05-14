"""Module implementing the Identity monad, the simplest monad that just wraps a value.

Examples:
    Create and use an Identity monad:
        >>> x = Identity(5)
        >>> x.get()
        5
        
    Map a function over an Identity:
        >>> x = Identity(5)
        >>> y = x.map(lambda n: n * 2)
        >>> y.get()
        10
        
    Chain Identity monads using bind:
        >>> x = Identity(5)
        >>> y = x.bind(lambda n: Identity(n * 2))
        >>> y.get()
        10
        
    Create an Identity using pure:
        >>> x = Identity.pure(5)
        >>> x.get()
        5
"""

from typing import TypeVar, Generic
from collections.abc import Callable

A = TypeVar("A")  # Input type
B = TypeVar("B")  # Output type


class Identity(Generic[A]):
    """Identity monad that simply wraps a value.
    
    The Identity monad is the simplest monad that just wraps a value and 
    provides monadic operations on it. It serves as a baseline for monadic 
    computations and can be useful as a building block for more complex monads.
    """
    
    def __init__(self, value: A) -> None:
        """Initialize an Identity monad with a value.
        
        Args:
            value: The value to wrap in the Identity monad.
        """
        self._value = value
    
    def map(self, f: Callable[[A], B]) -> "Identity[B]":
        """Apply a function to the wrapped value.
        
        Args:
            f: The function to apply to the value.
            
        Returns:
            A new Identity containing the result of applying f to the value.
        """
        return Identity(f(self._value))
    
    def bind(self, f: Callable[[A], "Identity[B]"]) -> "Identity[B]":
        """Chain this Identity with a function that returns another Identity.
        
        Args:
            f: A function that takes the value of this Identity and returns a new Identity.
            
        Returns:
            The Identity returned by the function f.
        """
        return f(self._value)
    
    def get(self) -> A:
        """Get the value wrapped by this Identity.
        
        Returns:
            The wrapped value.
        """
        return self._value
    
    @staticmethod
    def pure(value: A) -> "Identity[A]":
        """Create an Identity containing the given value.
        
        Args:
            value: The value to wrap in an Identity.
            
        Returns:
            An Identity containing the value.
        """
        return Identity(value)
    
    def __repr__(self) -> str:
        """Return a string representation of the Identity monad.
        
        Returns:
            A string representation of the Identity with its wrapped value.
        """
        return f"Identity({self._value})"