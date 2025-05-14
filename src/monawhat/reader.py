"""Module implementing the Reader monad for handling environment-based computations.

Examples:
    Basic usage of Reader monad:

    >>> # Create a Reader that reads a config value
    >>> get_db_url = Reader.asks(lambda config: config['db_url'])
    >>> # Create a Reader that uses the db_url
    >>> def get_user(user_id: int) -> Reader:
    ...     return get_db_url.map(lambda url: f"Fetching user {user_id} from {url}")
    >>> # Run the computation with a config
    >>> config = {'db_url': 'postgresql://localhost:5432'}
    >>> result = get_user(123).run(config)
    >>> print(result)
    'Fetching user 123 from postgresql://localhost:5432'

    Chaining Reader computations:

    >>> # Create Readers for different config values
    >>> get_host = Reader.asks(lambda config: config['host'])
    >>> get_port = Reader.asks(lambda config: config['port'])
    >>> # Combine them using bind
    >>> def get_address() -> Reader:
    ...     return get_host.bind(
    ...         lambda h: get_port.map(
    ...             lambda p: f"{h}:{p}"
    ...         )
    ...     )
    >>> # Run with config
    >>> config = {'host': 'localhost', 'port': 8080}
    >>> result = get_address().run(config)
    >>> print(result)
    'localhost:8080'
"""

from typing import TypeVar, Generic
from collections.abc import Callable

from monawhat.base import BaseMonad

E = TypeVar("E")  # Environment type
A = TypeVar("A")  # Input type
B = TypeVar("B")  # Output type


class Reader(Generic[E, A], BaseMonad[A]):
    """Reader monad for computations that read values from a shared environment.

    The Reader monad represents a computation that can read values from a shared environment
    and produce a result. It's useful for dependency injection and managing configurations.
    """

    def __init__(self, run_fn: Callable[[E], A]) -> None:
        """Initialize a Reader with a function that reads from an environment.

        Args:
            run_fn: A function that takes an environment and returns a value.
        """
        self._run_fn = run_fn

    def run(self, env: E) -> A:
        """Execute the Reader computation with the given environment.

        Args:
            env: The environment to run the computation in.

        Returns:
            The result of the computation.
        """
        return self._run_fn(env)

    def _map_implementation(self, f: Callable[[A], B]) -> "Reader[E, B]":
        """Apply a function to the result of this Reader.

        Args:
            f: The function to apply to the result.

        Returns:
            A new Reader that applies the function to the result.
        """
        return Reader(lambda env: f(self.run(env)))

    def _bind_implementation(self, f: Callable[[A], "Reader[E, B]"]) -> "Reader[E, B]":
        """Chain this Reader with a function that returns another Reader.

        Args:
            f: A function that takes the result of this Reader and returns a new Reader.

        Returns:
            A new Reader representing the chained computation.
        """
        return Reader(lambda env: f(self.run(env)).run(env))

    @classmethod
    def _pure_implementation(cls, value: A) -> "Reader[E, A]":
        """Create a Reader that ignores the environment and returns a fixed value.

        Args:
            value: The value to return.

        Returns:
            A Reader that always returns the given value.
        """
        return Reader(lambda _: value)

    @staticmethod
    def ask() -> "Reader[E, E]":
        """Create a Reader that returns the environment itself.

        Returns:
            A Reader that returns the environment it's run with.
        """
        return Reader(lambda env: env)

    @staticmethod
    def asks(f: Callable[[E], A]) -> "Reader[E, A]":
        """Create a Reader that applies a function to the environment.

        Args:
            f: A function to apply to the environment.

        Returns:
            A Reader that applies the function to the environment.
        """
        return Reader(f)

    def local(self, f: Callable[[E], E]) -> "Reader[E, A]":
        """Run this Reader in a modified environment.

        Args:
            f: A function that transforms the environment.

        Returns:
            A Reader that runs in the modified environment.
        """
        return Reader(lambda env: self.run(f(env)))

    def __repr__(self) -> str:
        """Return a string representation of the Reader."""
        return f"Reader({self._run_fn})"
