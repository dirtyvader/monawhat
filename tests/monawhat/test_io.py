"""Tests for the IO monad implementations."""

import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, TextIO, TypeVar
from unittest.mock import MagicMock, patch

from monawhat.either import Either
from monawhat.io import IO, IOLite

THE_RESPONSE = 42
HALF_RESPONSE = THE_RESPONSE // 2
TWENTY = HALF_RESPONSE - 1

TWO = 2
THREE = TWO + 1
FOUR = TWO * 2
ONE_THOUSAND = TWO * 500
T = TypeVar("T")


class TestIOLiteBasics:
    """Tests for the IOLite monad basic operations."""

    def test_init_and_run(self):
        """Test the initialization and running of an IOLite."""
        # Create an IOLite that returns a value
        io_lite = IOLite(lambda: THE_RESPONSE)
        result = io_lite.run()

        assert result == THE_RESPONSE

    def test_pure(self):
        """Test the pure factory method."""
        io_lite = IOLite.pure(THE_RESPONSE)
        result = io_lite.run()

        assert result == THE_RESPONSE

    def test_from_callable(self):
        """Test creating an IOLite from a callable."""

        def double(x: int) -> int:
            return x * 2

        io_lite = IOLite.from_callable(double, 21)
        result = io_lite.run()

        assert result == THE_RESPONSE

    def test_representation(self):
        """Test the string representation."""
        io_lite = IOLite(lambda: THE_RESPONSE)
        assert "IOLite" in repr(io_lite)


class TestIOLiteTransformations:
    """Tests for IOLite monad transformation methods."""

    def test_map(self):
        """Test mapping a function over an IOLite."""
        io_lite = IOLite(lambda: 21)
        mapped = io_lite.map(lambda x: x * 2)

        result = mapped.run()
        assert result == THE_RESPONSE

    def test_bind(self):
        """Test binding an IOLite to another function."""
        io_lite = IOLite(lambda: 21)

        def double(x: int) -> IOLite[int]:
            return IOLite(lambda: x * 2)

        bound = io_lite.bind(double)
        result = bound.run()

        assert result == THE_RESPONSE

    def test_chained_operations(self):
        """Test chaining multiple IOLite operations."""
        result = (
            IOLite.pure(10)
            .bind(lambda x: IOLite.pure(x + 5))
            .bind(lambda x: IOLite.pure(x * 2))
            .map(lambda x: x + 2)
            .run()
        )

        # (10 + 5) * 2 + 2 = 32, not THE_RESPONSE (42)
        assert result == THE_RESPONSE - 10


class TestIOLitePracticalUsage:
    """Tests demonstrating practical usage of the IOLite monad."""

    @patch("builtins.print")
    def test_io_effects_with_lite(self, mock_print):
        """Test using IOLite for simple IO effects."""

        # A function that returns an IOLite for printing
        def print_message(msg: str) -> IOLite[None]:
            return IOLite(lambda: print(msg))

        # A function that returns an IOLite for computation
        def compute(x: int) -> IOLite[int]:
            return IOLite(lambda: x * 2)

        # Chain the operations
        program = (
            compute(10).bind(
                lambda result: print_message(f"The result is {result}").map(
                    lambda _: result
                )
            )  # Return the result from compute
        )

        # Run the program
        result = program.run()

        # IOLite doesn't add default parameters unlike the full IO implementation
        mock_print.assert_called_once_with("The result is 20")
        assert result == TWENTY


class TestIOBasics:
    """Tests for the IO monad basic operations."""

    def test_init_and_run(self):
        """Test the initialization and running of an IO."""
        io = IO(lambda: THE_RESPONSE)
        result = io.run()

        assert result == THE_RESPONSE

    def test_pure(self):
        """Test the pure factory method."""
        io = IO.pure(THE_RESPONSE)
        result = io.run()

        assert result == THE_RESPONSE

    def test_fail(self):
        """Test the fail factory method."""
        io = IO.fail(ValueError("Test error"))

        try:
            io.run()
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "Test error" in str(e)

    def test_from_callable(self):
        """Test creating an IO from a callable."""

        def double(x: int) -> int:
            return x * 2

        io = IO.from_callable(double, 21)
        result = io.run()

        assert result == THE_RESPONSE

    def test_representation(self):
        """Test the string representation."""
        io = IO(lambda: THE_RESPONSE)
        assert "IO" in repr(io)


class TestIOTransformations:
    """Tests for IO monad transformation methods."""

    def test_map(self):
        """Test mapping a function over an IO."""
        io = IO(lambda: 21)
        mapped = io.map(lambda x: x * 2)

        result = mapped.run()
        assert result == THE_RESPONSE

    def test_bind(self):
        """Test binding an IO to another function."""
        io = IO(lambda: 21)

        def double(x: int) -> IO[int]:
            return IO(lambda: x * 2)

        bound = io.bind(double)
        result = bound.run()

        assert result == THE_RESPONSE

    def test_then(self):
        """Test the then method for sequential execution."""
        # Create a mutable counter to verify execution order
        counter = {"value": 0}

        io1 = IO(lambda: counter.update({"value": counter["value"] + 1}))
        io2 = IO(lambda: counter.update({"value": counter["value"] * 2}))

        # Run io1 then io2, keep io2's result
        result = io1.then(io2).run()

        # The counter should be incremented then doubled: (0+1)*2 = 2
        assert counter["value"] == TWO
        assert result is None  # io2 returns None

    def test_attempt(self):
        """Test the attempt method for error handling."""
        # IO that succeeds
        success = IO(lambda: THE_RESPONSE).attempt().run()
        assert success.is_right()
        assert success.get() == THE_RESPONSE

        # IO that fails
        error_message = "Test error"
        failure = (
            IO(lambda: (_ for _ in ()).throw(ValueError(error_message))).attempt().run()
        )
        assert failure.is_left()
        assert isinstance(failure.get(), ValueError)
        assert error_message in str(failure.get())

    def test_map_error(self):
        """Test the map_error method for transforming exceptions."""

        def transform_error(e: Exception) -> Exception:
            return RuntimeError(f"Transformed: {str(e)}")

        io = IO(lambda: (_ for _ in ()).throw(ValueError("Original error")))
        transformed = io.map_error(transform_error)

        try:
            transformed.run()
            assert False, "Expected RuntimeError to be raised"
        except RuntimeError as e:
            assert "Transformed: Original error" in str(e)

    def test_catch(self):
        """Test the catch method for handling exceptions."""

        def handle_error(e: Exception) -> IO[int]:
            return IO.pure(THE_RESPONSE)

        # IO that fails but is caught
        io = IO(lambda: (_ for _ in ()).throw(ValueError("Original error")))
        result = io.catch(handle_error).run()

        assert result == THE_RESPONSE

    def test_with_finally(self):
        """Test the with_finally method."""
        cleanup_called = {"value": False}
        finalizer = IO(lambda: cleanup_called.update({"value": True}))

        # Success case
        IO.pure(THE_RESPONSE).with_finally(finalizer).run()
        assert cleanup_called["value"] is True

        # Reset flag
        cleanup_called["value"] = False

        # Failure case
        try:
            IO(lambda: (_ for _ in ()).throw(ValueError("Test error"))).with_finally(
                finalizer
            ).run()
        except ValueError:
            pass

        assert cleanup_called["value"] is True


class TestIOUtilities:
    """Tests for IO utility methods."""

    @patch("builtins.print")
    def test_print(self, mock_print):
        """Test the print utility."""
        message = "Hello, world!"
        IO.print(message).run()
        mock_print.assert_called_once_with(message, end="\n", file=sys.stdout)

        # Test with custom end and file
        mock_file = MagicMock(spec=TextIO)
        IO.print(message, end="!", file=mock_file).run()
        mock_print.assert_called_with(message, end="!", file=mock_file)

    @patch("builtins.input", return_value="test input")
    def test_input(self, mock_input):
        """Test the input utility."""
        prompt = "Enter something: "
        result = IO.input(prompt).run()

        mock_input.assert_called_once_with(prompt)
        assert result == "test input"

    def test_sequence(self):
        """Test the sequence utility."""
        ios = [IO.pure(1), IO.pure(2), IO.pure(3)]
        result = IO.sequence(ios).run()

        assert result == [1, 2, 3]

    def test_traverse(self):
        """Test the traverse utility."""
        numbers = [1, 2, 3]
        result = IO.traverse(numbers, lambda x: IO.pure(x * 2)).run()

        assert result == [2, 4, 6]

    def test_for_each(self):
        """Test the for_each utility."""
        calls = []

        def record(x: int) -> IO[None]:
            return IO(lambda: calls.append(x))

        IO.for_each([1, 2, 3], record).run()
        assert calls == [1, 2, 3]

    @patch("asyncio.run")
    def test_async_to_io(self, mock_run):
        """Test the async_to_io utility."""
        mock_run.return_value = THE_RESPONSE

        # Make a reference to store the created coroutine
        created_coro = None

        # Override asyncio.run to capture and store the coroutine
        def capture_coro(coro):
            nonlocal created_coro
            created_coro = coro
            return THE_RESPONSE

        mock_run.side_effect = capture_coro

        async def async_func(x: int) -> int:
            return x * 2

        result = IO.async_to_io(async_func, 21).run()

        # Verify mock_run was called
        mock_run.assert_called_once()
        assert result == THE_RESPONSE

        # Clean up the coroutine to prevent the warning
        if created_coro is not None:
            created_coro.close()

    def test_with_context_io(self):
        """Test the with_context_io utility."""

        @contextmanager
        def dummy_context() -> Generator[int, None, None]:
            yield THE_RESPONSE

        result = IO.with_context_io(dummy_context()).run()
        assert result == THE_RESPONSE


class TestIOEither:
    """Tests for combining IO with Either."""

    def test_io_either_bind(self):
        """Test binding IO[Either] operations."""
        from monawhat.io import io_either_bind

        # Create an IO that returns a Right
        io_right = IO.pure(Either.right(21))

        # Function that takes a value and returns an IO[Either]
        def double(x: int) -> IO[Either[str, int]]:
            return IO.pure(Either.right(x * 2))

        # Bind them together
        result = io_either_bind(io_right, double).run()

        assert result.is_right()
        assert result.get() == THE_RESPONSE

        # Try with a Left
        io_left = IO.pure(Either.left("error"))
        result = io_either_bind(io_left, double).run()

        assert result.is_left()
        assert result.get() == "error"


class TestIOPracticalUsage:
    """Tests demonstrating practical usage of the IO monad."""

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["21", "2"])
    def test_calculator(self, mock_input, mock_print):
        """Test a simple calculator program using IO."""

        # Define the program
        def calculator() -> IO[int]:
            return (
                IO.print("Enter first number:")
                .then(IO.input())
                .bind(
                    lambda a_str: IO.print("Enter second number:")
                    .then(IO.input())
                    .bind(lambda b_str: IO.pure(int(a_str) * int(b_str)))
                )
                .bind(
                    lambda result: IO.print(f"The result is: {result}").map(
                        lambda _: result
                    )
                )
            )

        # Run the program
        result = calculator().run()

        # Verify the interactions
        assert mock_input.call_count == TWO
        assert mock_print.call_count == THREE
        assert result == THE_RESPONSE  # 21 * 2 = 42

    @patch("builtins.print")
    def test_error_handling(self, mock_print):
        """Test error handling with the IO monad."""

        def operation_that_may_fail(x: int) -> IO[int]:
            if x == 0:
                return IO.fail(ValueError("Cannot divide by zero"))
            return IO.pure(42 // x)  # Integer division

        # The successful case
        success_program = operation_that_may_fail(2).bind(
            lambda result: IO.print(f"Result: {result}").map(lambda _: result)
        )
        success_result = success_program.run()
        mock_print.assert_called_with("Result: 21", end="\n", file=sys.stdout)
        assert success_result == HALF_RESPONSE

        mock_print.reset_mock()

        # The error case with proper handling
        error_program = operation_that_may_fail(0).catch(
            lambda e: IO.print(f"Error occurred: {e}").then(
                IO.pure(-1)
            )  # Return -1 on error
        )
        error_result = error_program.run()
        mock_print.assert_called_with(
            "Error occurred: Cannot divide by zero", end="\n", file=sys.stdout
        )
        assert error_result == -1

        mock_print.reset_mock()

        # Using attempt for Either-based error handling
        attempt_program = (
            operation_that_may_fail(0)
            .attempt()
            .bind(
                lambda either: IO.print(
                    f"Either caught: {either.get()}"
                    if either.is_left()
                    else f"Success: {either.get()}"
                ).then(IO.pure(-1 if either.is_left() else either.get()))
            )
        )
        attempt_result = attempt_program.run()
        mock_print.assert_called_with(
            "Either caught: Cannot divide by zero", end="\n", file=sys.stdout
        )
        assert attempt_result == -1

    def test_composing_io_operations(self):
        """Test composing multiple IO operations."""
        results = []

        def record(label: str, value: Any) -> IO[Any]:
            return IO(lambda: results.append((label, value))).map(lambda _: value)

        program = (
            IO.pure(10)
            .bind(lambda x: record("step1", x))
            .map(lambda x: x * 2)
            .bind(lambda x: record("step2", x))
            .map(lambda x: x + 2)
            .bind(lambda x: record("final", x))
        )

        result = program.run()

        # 10 * 2 + 2 = 22, not THE_RESPONSE (42)
        assert result == TWENTY + 2
        assert results == [("step1", 10), ("step2", 20), ("final", 22)]

    @patch("builtins.print")
    def test_conditional_io(self, mock_print):
        """Test conditional IO operations."""

        def process_number(n: int) -> IO[int]:
            if n % 2 == 0:
                return IO.print(f"{n} is even").then(IO.pure(n * 2))
            else:
                return IO.print(f"{n} is odd").then(IO.pure(n + 1))

        # Test with even number
        even_result = process_number(2).run()
        mock_print.assert_called_with("2 is even", end="\n", file=sys.stdout)
        assert even_result == FOUR

        mock_print.reset_mock()

        # Test with odd number
        odd_result = process_number(3).run()
        mock_print.assert_called_with("3 is odd", end="\n", file=sys.stdout)
        assert odd_result == FOUR

    @patch("builtins.print")
    def test_retry_mechanism(self, mock_print):
        """Test implementing a retry mechanism with IO."""
        attempt_count = {"value": 0}

        def operation_with_retries(max_retries: int) -> IO[str]:
            def attempt() -> IO[Either[Exception, str]]:
                return IO(
                    lambda: (
                        attempt_count.update({"value": attempt_count["value"] + 1}),
                        Either.left(ValueError("Failed"))
                        if attempt_count["value"] < THREE
                        else Either.right("Success"),
                    )[1]
                )

            def retry(retries_left: int) -> IO[str]:
                return attempt().bind(
                    lambda result:
                    # Always print a message for failed attempts, not just when out of retries
                    IO.print(
                        f"Attempt failed ({max_retries - retries_left + 1}): {result.get()}"
                    ).then(
                        IO.pure("Failed")
                        if retries_left <= 0
                        else retry(retries_left - 1)
                    )
                    if result.is_left()
                    else IO.pure(result.get())
                )

            return retry(max_retries)

        # This should succeed after 3 attempts
        result = operation_with_retries(5).run()
        assert result == "Success"
        assert attempt_count["value"] == THREE  # It took 3 attempts
        assert mock_print.call_count == TWO  # Two failure messages

    def test_resource_management(self):
        """Test resource management pattern with IO."""
        resource_state = {"initialized": False, "closed": False, "operations": []}

        # Simulate a resource manager
        def init_resource() -> IO[dict]:
            return IO(
                lambda: (resource_state.update({"initialized": True}), resource_state)[
                    1
                ]
            )

        def use_resource(resource: dict, operation: str) -> IO[dict]:
            return IO(
                lambda: (resource["operations"].append(operation), resource)[1]
                if resource["initialized"] and not resource["closed"]
                else (_ for _ in ()).throw(ValueError("Resource not available"))
            )

        def close_resource(resource: dict) -> IO[None]:
            return IO(lambda: resource.update({"closed": True}))

        # Using with_finally for resource cleanup
        program = init_resource().bind(
            lambda r: use_resource(r, "operation1")
            .bind(lambda _: use_resource(r, "operation2"))
            .with_finally(close_resource(r))
        )

        program.run()

        assert resource_state["initialized"] is True
        assert resource_state["closed"] is True
        assert resource_state["operations"] == ["operation1", "operation2"]

        # Test with error during operations
        resource_state = {"initialized": False, "closed": False, "operations": []}

        def failing_operation(resource: dict) -> IO[None]:
            return IO(lambda: (_ for _ in ()).throw(RuntimeError("Operation failed")))

        program_with_error = (
            init_resource()
            .bind(
                lambda r: use_resource(r, "operation1")
                .bind(lambda _: failing_operation(r))
                .with_finally(close_resource(r))
            )
            .catch(lambda _: IO.pure(None))  # Catch the error
        )

        program_with_error.run()

        # Resource should still be properly initialized and closed
        assert resource_state["initialized"] is True
        assert resource_state["closed"] is True
        assert resource_state["operations"] == [
            "operation1"
        ]  # Only first operation completed


class TestIOEdgeCases:
    """Tests for edge cases in the IO monad implementation."""

    def test_nested_binds(self):
        """Test deeply nested binds."""
        depth = 100
        io = IO.pure(0)

        # Create a deeply nested chain of binds
        for i in range(depth):
            io = io.bind(lambda x, i=i: IO.pure(x + 1))

        result = io.run()
        assert result == depth

    def test_stack_safety(self):
        """Test stack safety with many operations."""
        # Create a list of 1000 IO operations
        ios = [IO.pure(i) for i in range(1000)]

        # Sequence them all
        result = IO.sequence(ios).run()

        assert len(result) == ONE_THOUSAND
        assert result[42] == THE_RESPONSE

    def test_empty_sequence(self):
        """Test sequencing an empty list."""
        result = IO.sequence([]).run()
        assert result == []

    def test_exception_during_map(self):
        """Test that exceptions during map are properly propagated."""
        io = IO.pure(42)

        def failing_function(x):
            raise ValueError("Map failed")

        mapped = io.map(failing_function)

        try:
            mapped.run()
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "Map failed" in str(e)
