"""Module implementing IO monads for handling input/output operations.

Examples:
    Basic IOLite usage:

    >>> from monawhat.io import IOLite
    >>> read_name = IOLite.from_callable(input, "Enter name: ")
    >>> greet = read_name.map(lambda name: f"Hello, {name}!")
    >>> greet.run()  # Executes the IO operation

    Full IO with error handling:

    >>> from monawhat.io import IO
    >>> def divide(x: int, y: int) -> IO[float]:
    ...     return IO.from_callable(lambda: x / y)
    >>> safe_divide = divide(10, 0).attempt()
    >>> result = safe_divide.run()  # Returns Either[Exception, float]

    IO composition:

    >>> get_input = IO.input("Enter text: ")
    >>> print_upper = get_input.map(str.upper).bind(IO.print)
    >>> print_upper.run()  # Gets input and prints it in uppercase

    Error handling with catch:

    >>> def safe_operation() -> IO[str]:
    ...     return IO.from_callable(lambda: some_risky_operation()).catch(
    ...         lambda e: IO.pure("Operation failed")
    ...     )
"""
from typing import TypeVar, cast, TextIO, Any
from contextlib import AbstractContextManager
from collections.abc import Callable, Awaitable, Coroutine
import asyncio
import sys
# import os

from monawhat.base import BaseMonad
from monawhat.either import Either

A = TypeVar("A")  # Result type
B = TypeVar("B")  # Another result type
E = TypeVar("E")  # Error type
T = TypeVar("T")  # Type of the value yielded by the context manager


class IOLite(BaseMonad[A]):
    """Lightweight IO monad for representing and composing IO operations.

    This is a minimal implementation focused on core monad operations.
    For a more feature-rich implementation, see the IO class.
    """

    def __init__(self, effect: Callable[[], A]) -> None:
        """Initialize an IOLite monad with an effect function."""
        self._effect = effect

    def run(self) -> A:
        """Execute the IO operation and return its result."""
        return self._effect()

    def _map_implementation(self, f: Callable[[A], B]) -> "IOLite[B]":
        """Apply a function to the result of this IO operation."""
        return IOLite(lambda: f(self.run()))

    def _bind_implementation(self, f: Callable[[A], "IOLite[B]"]) -> "IOLite[B]":
        """Chain this IO with a function that returns another IO."""
        return IOLite(lambda: f(self.run()).run())

    @classmethod
    def _pure_implementation(cls, value: A) -> "IOLite[A]":
        """Create an IO that returns a fixed value without performing IO."""
        return IOLite(lambda: value)

    @staticmethod
    def from_callable(
        io_operation: Callable[..., A], *args: Any, **kwargs: Any
    ) -> "IOLite[A]":
        """Create an IO from any callable."""
        return IOLite(lambda: io_operation(*args, **kwargs))

    def __repr__(self) -> str:
        """Return a string representation of the IO."""
        return f"IOLite({self._effect})"


class IO(BaseMonad[A]):
    """IO monad for representing and composing IO operations.

    The IO monad represents a computation that may perform input/output operations
    and produce a value. It's useful for making IO explicit and composable.

    Unlike in Haskell, this IO monad doesn't enforce purity - it's primarily for
    composition and making effects more explicit.
    """

    def __init__(self, effect: Callable[[], A]) -> None:
        """Initialize an IO monad with an effect function.

        Args:
            effect: A function that performs IO and returns a value
        """
        self._effect = effect

    def run(self) -> A:
        """Execute the IO operation and return its result.

        Returns:
            The result of the IO operation
        """
        return self._effect()

    def _map_implementation(self, f: Callable[[A], B]) -> "IO[B]":
        """Apply a function to the result of this IO operation.

        Args:
            f: The function to apply to the result

        Returns:
            A new IO that applies the function to the result
        """
        return IO(lambda: f(self.run()))

    def _bind_implementation(self, f: Callable[[A], "IO[B]"]) -> "IO[B]":
        """Chain this IO with a function that returns another IO.

        Args:
            f: A function that takes the result of this IO and returns a new IO

        Returns:
            A new IO representing the chained computation
        """
        return IO(lambda: f(self.run()).run())

    def then(self, io: "IO[B]") -> "IO[B]":
        """Execute this IO, ignore its result, and then execute another IO.

        Args:
            io: The IO operation to execute after this one

        Returns:
            A new IO that represents the sequential execution
        """
        return IO(lambda: (self.run(), io.run())[1])

    def map_error(self, f: Callable[[Exception], Exception]) -> "IO[A]":
        """Transform any exception thrown by this IO operation.

        Args:
            f: A function that transforms exceptions

        Returns:
            A new IO that transforms exceptions
        """

        def new_effect() -> A:
            try:
                return self.run()
            except Exception as e:
                raise f(e) from e

        return IO(new_effect)

    def catch(self, handler: Callable[[Exception], "IO[A]"]) -> "IO[A]":
        """Catch exceptions thrown by this IO and handle them with the provided function.

        Args:
            handler: A function that takes an exception and returns an IO

        Returns:
            A new IO that catches and handles exceptions
        """

        def new_effect() -> A:
            try:
                return self.run()
            except Exception as e:
                return handler(e).run()

        return IO(new_effect)

    def attempt(self) -> "IO[Either[Exception, A]]":
        """Convert this IO into one that returns an Either for error handling.

        Returns:
            An IO that returns Either a Left with the exception or a Right with the result
        """
        from monawhat.either import Either

        def new_effect() -> Either[Exception, A]:
            try:
                return Either.right(self.run())
            except Exception as e:
                return Either.left(e)

        return IO(new_effect)

    def with_finally(self, finalizer: "IO[Any]") -> "IO[A]":
        """Ensure the finalizer runs regardless of whether this IO succeeds or fails.

        Args:
            finalizer: The IO to run after this IO, regardless of outcome

        Returns:
            A new IO that runs the finalizer after this IO
        """

        def new_effect() -> A:
            try:
                return self.run()
            finally:
                finalizer.run()

        return IO(new_effect)

    @classmethod
    def _pure_implementation(cls, value: A) -> "IO[A]":
        """Create an IO that returns a fixed value without performing IO.

        Args:
            value: The value to return

        Returns:
            An IO that returns the given value
        """
        return IO(lambda: value)

    @staticmethod
    def fail(exception: Exception) -> "IO[A]":
        """Create an IO that raises an exception when run.

        Args:
            exception: The exception to raise

        Returns:
            An IO that raises the exception
        """

        def fail_effect() -> A:
            raise exception

        return IO(fail_effect)

    @staticmethod
    def from_callable(
        io_operation: Callable[..., A], *args: Any, **kwargs: Any
    ) -> "IO[A]":
        """Create an IO from any callable.

        Args:
            io_operation: The function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            An IO that calls the function
        """
        return IO(lambda: io_operation(*args, **kwargs))

    @staticmethod
    def print(message: str, end: str = "\n", file: TextIO | None = None) -> "IO[None]":
        """Create an IO that prints a message.

        Args:
            message: The message to print
            end: The string to append after the message
            file: The file to print to (defaults to sys.stdout)

        Returns:
            An IO that prints the message
        """
        return IO(lambda: print(message, end=end, file=file or sys.stdout))

    @staticmethod
    def input(prompt: str = "") -> "IO[str]":
        """Create an IO that reads a line from stdin.

        Args:
            prompt: The prompt to display

        Returns:
            An IO that reads a line
        """
        return IO(lambda: input(prompt))

    ## TODO: move to monawhat_extras
    # @staticmethod
    # def read_file(
    #     file_path: str, mode: str = "r", encoding: str | None = None
    # ) -> "IO[str]":
    #     """Create an IO that reads a file.

    #     Args:
    #         file_path: The path to the file
    #         mode: The mode to open the file in
    #         encoding: The encoding to use

    #     Returns:
    #         An IO that reads the file
    #     """

    #     def read_effect() -> str:
    #         with open(file_path, mode, encoding=encoding) as f:
    #             return f.read()

    #     return IO(read_effect)

    # @staticmethod
    # def write_file(
    #     file_path: str, content: str, mode: str = "w", encoding: str | None = None
    # ) -> "IO[None]":
    #     """Create an IO that writes to a file.

    #     Args:
    #         file_path: The path to the file
    #         content: The content to write
    #         mode: The mode to open the file in
    #         encoding: The encoding to use

    #     Returns:
    #         An IO that writes to the file
    #     """

    #     def write_effect() -> None:
    #         with open(file_path, mode, encoding=encoding) as f:
    #             f.write(content)

    #     return IO(write_effect)

    # @staticmethod
    # def append_file(
    #     file_path: str, content: str, encoding: str | None = None
    # ) -> "IO[None]":
    #     """Create an IO that appends to a file.

    #     Args:
    #         file_path: The path to the file
    #         content: The content to append
    #         encoding: The encoding to use

    #     Returns:
    #         An IO that appends to the file
    #     """
    #     return IO.write_file(file_path, content, "a", encoding)

    # @staticmethod
    # def list_dir(dir_path: str) -> "IO[list[str]]":
    #     """Create an IO that lists the contents of a directory.

    #     Args:
    #         dir_path: The path to the directory

    #     Returns:
    #         An IO that lists the directory contents
    #     """
    #     return IO.from_callable(os.listdir, dir_path)

    @staticmethod
    def with_context_io(ctx_manager: AbstractContextManager[T]) -> "IO[T]":
        """Create an IO from a context manager.

        This allows using Python's context managers within the IO monad.

        Args:
            ctx_manager: The context manager that yields a value of type T

        Returns:
            An IO that represents the context manager's yielded value
        """

        def cm_effect() -> T:
            with ctx_manager as value:
                return value

        return IO(cm_effect)

    @staticmethod
    def sequence(ios: list["IO[A]"]) -> "IO[list[A]]":
        """Execute a list of IO operations in sequence and collect their results.

        Args:
            ios: A list of IO operations

        Returns:
            An IO that returns a list of results
        """

        def sequence_effect() -> list[A]:
            return [io.run() for io in ios]

        return IO(sequence_effect)

    @staticmethod
    def traverse(xs: list[A], f: Callable[[A], "IO[B]"]) -> "IO[list[B]]":
        """Apply an IO-producing function to each element in a list and collect the results.

        Args:
            xs: A list of values
            f: A function that takes a value and returns an IO

        Returns:
            An IO that returns a list of results
        """

        def traverse_effect() -> list[B]:
            return [f(x).run() for x in xs]

        return IO(traverse_effect)

    @staticmethod
    def for_each(xs: list[A], f: Callable[[A], "IO[B]"]) -> "IO[None]":
        """Apply an IO-producing function to each element in a list for its effects.

        Args:
            xs: A list of values
            f: A function that takes a value and returns an IO

        Returns:
            An IO that executes each operation for its effect
        """

        def for_each_effect() -> None:
            for x in xs:
                f(x).run()

        return IO(for_each_effect)

    @staticmethod
    def async_to_io(
        coro: Callable[..., Awaitable[A]], *args: Any, **kwargs: Any
    ) -> "IO[A]":
        """Convert an async function to an IO.

        Args:
            coro: An async function
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            An IO that runs the async function
        """

        def run_async() -> A:
            return asyncio.run(cast(Coroutine[Any, Any, A], coro(*args, **kwargs)))

        return IO(run_async)

    def __repr__(self) -> str:
        """Return a string representation of the IO."""
        return f"IO({self._effect})"


# Utility for combining with Either monad
def io_either_bind(
    io_either: IO[Either[E, A]], f: Callable[[A], IO[Either[E, B]]]
) -> IO[Either[E, B]]:
    """Bind an IO[Either] with a function that takes the Right value and returns another IO[Either].

    This is useful for chaining operations that can fail.

    Args:
        io_either: An IO that returns an Either
        f: A function that takes the success value and returns an IO[Either]

    Returns:
        An IO that returns the final Either
    """
    from monawhat.either import Either, Left

    def run_io() -> Either[E, B]:
        either = io_either.run()
        if either.is_right():
            return f(cast(A, either.get())).run()
        else:
            return cast(Left[E, B], either)

    return IO(run_io)
