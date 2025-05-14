"""Module implementing the State monad for handling stateful computations.

Examples:
    Basic usage of State monad:

    >>> # Create a state that increments a counter and returns the old value
    >>> def increment() -> State[int, int]:
    ...     return State(lambda s: (s, s + 1))
    ...
    >>> # Chain multiple state operations
    >>> computation = increment().bind(
    ...     lambda x: increment().bind(
    ...         lambda y: State.pure(x + y)
    ...     )
    ... )
    >>> # Run the computation with initial state 0
    >>> result, final_state = computation.run(0)
    >>> print(result)  # Sum of first two states: 0 + 1 = 1
    1
    >>> print(final_state)  # Final counter value: 2

    Using helper methods:
    
    >>> # Get current state
    >>> get_state = State.get()
    >>> value, state = get_state.run(42)
    >>> assert value == state == 42
    
    >>> # Modify state
    >>> add_one = State.modify(lambda x: x + 1)
    >>> _, new_state = add_one.run(10)
    >>> assert new_state == 11
"""

from typing import TypeVar, Generic
from collections.abc import Callable

from monawhat.base import BaseMonad

S = TypeVar("S")  # State type
A = TypeVar("A")  # Input type
B = TypeVar("B")  # Output type


class State(Generic[S, A], BaseMonad[A]):
    """State monad for computations that manipulate state.
    
    The State monad represents a stateful computation that produces a value and
    potentially modifies some state. It's useful for modeling computations with
    mutable state in a purely functional way.
    
    A State[S, A] instance represents a function from state S to a tuple (A, S),
    where A is the result value and S is the new state.
    """
    
    def __init__(self, run_fn: Callable[[S], tuple[A, S]]) -> None:
        """Initialize a State monad with a state transition function.
        
        Args:
            run_fn: A function that takes a state and returns a tuple of (value, new_state)
        """
        self._run_fn = run_fn
    
    def run(self, initial_state: S) -> tuple[A, S]:
        """Execute the stateful computation with the given initial state.
        
        Args:
            initial_state: The starting state
            
        Returns:
            A tuple containing the result value and the final state
        """
        return self._run_fn(initial_state)
    
    def eval(self, initial_state: S) -> A:
        """Execute the computation and return only the result value.
        
        Args:
            initial_state: The starting state
            
        Returns:
            The result value
        """
        value, _ = self.run(initial_state)
        return value
    
    def exec(self, initial_state: S) -> S:
        """Execute the computation and return only the final state.
        
        Args:
            initial_state: The starting state
            
        Returns:
            The final state
        """
        _, final_state = self.run(initial_state)
        return final_state
    
    def _map_implementation(self, f: Callable[[A], B]) -> "State[S, B]":
        """Apply a function to the result value while preserving the state.
        
        Args:
            f: The function to apply to the result value
            
        Returns:
            A new State that applies the function to the result
        """
        def new_run(s: S) -> tuple[B, S]:
            value, new_state = self.run(s)
            return f(value), new_state
        
        return State(new_run)
    
    def _bind_implementation(self, f: Callable[[A], "State[S, B]"]) -> "State[S, B]":
        """Chain this State with a function that returns another State.
        
        Args:
            f: A function that takes the result of this State and returns a new State
            
        Returns:
            A new State representing the chained computation
        """
        def new_run(s: S) -> tuple[B, S]:
            value, intermediate_state = self.run(s)
            return f(value).run(intermediate_state)
        
        return State(new_run)
    
    @classmethod
    def _pure_implementation(cls, value: A) -> "State[S, A]":
        """Create a State that returns the value without modifying the state.
        
        Args:
            value: The value to return
            
        Returns:
            A State that leaves the state unchanged and returns the value
        """
        return State(lambda s: (value, s))
    
    @staticmethod
    def get() -> "State[S, S]":
        """Create a State that returns the current state as its value.
        
        Returns:
            A State that returns the current state as its value
        """
        return State(lambda s: (s, s))
    
    @staticmethod
    def gets(f: Callable[[S], A]) -> "State[S, A]":
        """Create a State that applies a function to the current state to produce a value.
        
        Args:
            f: A function that computes a value from the state
            
        Returns:
            A State that applies the function to the current state
        """
        return State(lambda s: (f(s), s))
    
    @staticmethod
    def put(new_state: S) -> "State[S, None]":
        """Create a State that replaces the current state.
        
        Args:
            new_state: The new state to use
            
        Returns:
            A State that replaces the current state
        """
        return State(lambda _: (None, new_state))
    
    @staticmethod
    def modify(f: Callable[[S], S]) -> "State[S, None]":
        """Create a State that modifies the current state using a function.
        
        Args:
            f: A function that transforms the state
            
        Returns:
            A State that applies the function to the current state
        """
        return State(lambda s: (None, f(s)))
    
    def __repr__(self) -> str:
        """Return a string representation of the State."""
        return f"State({self._run_fn})"