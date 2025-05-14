"""Tests for the State monad."""

from monawhat.state import State
from typing import TypeVar, Any

THE_RESPONSE = 42
HALF_RESPONSE = THE_RESPONSE / 2
INITIAL_STATE = {"count": 0, "history": []}
THREE = 3
FIFTEEN = 15
FOURTEEN = FIFTEEN - 1
FIVE = 5
SIXTY = FIVE * 12

# Type variable for tests
T = TypeVar("T")


class TestStateBasics:
    """Tests for the State monad basic operations."""

    def test_init_and_run(self):
        """Test the initialization and running of a State."""
        # Create a state transition that increments a counter
        state = State(lambda s: (s["count"] + 1, {**s, "count": s["count"] + 1}))
        value, new_state = state.run(INITIAL_STATE)

        assert value == 1
        assert new_state["count"] == 1
        assert new_state != INITIAL_STATE  # State is immutable

    def test_eval_exec(self):
        """Test the eval and exec methods."""
        state = State(lambda s: (s["count"] * 2, {**s, "count": s["count"] + 1}))

        # eval should return only the value
        assert state.eval(INITIAL_STATE) == 0

        # exec should return only the state
        new_state = state.exec(INITIAL_STATE)
        assert new_state["count"] == 1
        assert "history" in new_state


class TestStateFactoryMethods:
    """Tests for the State monad factory methods."""

    def test_pure(self):
        """Test the pure factory method."""
        # Create a state with pure
        state = State.pure(THE_RESPONSE)
        value, new_state = state.run(INITIAL_STATE)

        assert value == THE_RESPONSE
        assert new_state == INITIAL_STATE  # State unchanged

    def test_get(self):
        """Test the get factory method."""
        # Get returns the current state as the value
        state = State.get()
        value, new_state = state.run(INITIAL_STATE)

        assert value == INITIAL_STATE
        assert new_state == INITIAL_STATE  # State unchanged

    def test_gets(self):
        """Test the gets factory method."""
        # Gets applies a function to the state
        state = State.gets(lambda s: s["count"] + THE_RESPONSE)
        value, new_state = state.run(INITIAL_STATE)

        assert value == THE_RESPONSE  # 0 + 42
        assert new_state == INITIAL_STATE  # State unchanged

    def test_put(self):
        """Test the put factory method."""
        # Put replaces the state
        new_state_value = {"count": 10, "history": ["reset"]}
        state = State.put(new_state_value)
        value, new_state = state.run(INITIAL_STATE)

        assert value is None
        assert new_state == new_state_value

    def test_modify(self):
        """Test the modify factory method."""
        # Modify transforms the state with a function
        state = State.modify(lambda s: {**s, "count": s["count"] + 1})
        value, new_state = state.run(INITIAL_STATE)

        assert value is None
        assert new_state["count"] == 1


class TestStateTransformations:
    """Tests for State monad transformation methods."""

    def test_map(self):
        """Test mapping a function over a State."""
        # Create a state that returns the current count
        state = State.gets(lambda s: s["count"])
        # Map a function to double the value
        mapped = state.map(lambda x: x * 2 + THE_RESPONSE)

        value, new_state = mapped.run({"count": HALF_RESPONSE})
        assert value == THE_RESPONSE + THE_RESPONSE  # 21*2 + 42 = 84
        assert new_state == {"count": HALF_RESPONSE}  # State unchanged

    def test_bind(self):
        """Test binding a State to another function."""
        # Start with a state that gets the count
        state = State.gets(lambda s: s["count"])

        # Function that returns a state to increment by the given value
        def increment_by(x):
            return State(lambda s: (x + 1, {**s, "count": s["count"] + x}))

        # Bind the two together
        bound = state.bind(increment_by)
        value, new_state = bound.run({"count": HALF_RESPONSE})

        assert value == HALF_RESPONSE + 1
        assert new_state["count"] == HALF_RESPONSE * 2  # 21 + 21 = 42

    def test_chained_binds(self):
        """Test chaining multiple binds."""

        # Define a state operation to increment and track history
        def increment(amount):
            return State(
                lambda s: (
                    s["count"] + amount,
                    {
                        **s,
                        "count": s["count"] + amount,
                        "history": s["history"] + [f"Added {amount}"],
                    },
                )
            )

        # Chain multiple operations
        result = (
            State.pure(0)
            .bind(lambda _: increment(10))
            .bind(lambda _: increment(15))
            .bind(lambda _: increment(17))
        )

        value, final_state = result.run(INITIAL_STATE)

        assert value == THE_RESPONSE  # 0 + 10 + 15 + 17 = 42
        assert final_state["count"] == THE_RESPONSE
        assert len(final_state["history"]) == THREE
        assert final_state["history"] == ["Added 10", "Added 15", "Added 17"]


class TestPracticalUsage:
    """Tests demonstrating practical usage of the State monad."""

    def test_counter_with_validation(self):
        """Test using State for a counter with validation."""

        def increment_if_positive(amount: int) -> State[dict[str, Any], bool]:
            """Increment counter only if it would remain positive."""

            def run_increment(s: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
                if s["count"] + amount >= 0:
                    return True, {
                        **s,
                        "count": s["count"] + amount,
                        "history": s["history"] + [f"Added {amount}"],
                    }
                else:
                    return False, {
                        **s,
                        "history": s["history"]
                        + [f"Rejected {amount} (would be negative)"],
                    }

            return State(run_increment)

        # Try a series of operations
        operations = State.pure(None)

        # Chain operations with different amounts
        operations = operations.bind(lambda _: increment_if_positive(5))
        operations = operations.bind(
            lambda succeeded: increment_if_positive(10)
            if succeeded
            else State.pure(False)
        )
        operations = operations.bind(
            lambda succeeded: increment_if_positive(-20)
            if succeeded
            else State.pure(False)
        )
        operations = operations.bind(
            lambda succeeded: increment_if_positive(5)
            if succeeded
            else State.pure(False)
        )

        # Run the combined state
        success, final_state = operations.run({"count": 0, "history": []})

        assert success is False  # The -20 operation should fail
        assert final_state["count"] == FIFTEEN  # 0 + 5 + 10
        assert any("Rejected -20" in entry for entry in final_state["history"])

    def test_stack_machine(self):
        """Test implementing a simple stack machine with the State monad."""

        # Define stack machine operations
        def push(value: int) -> State[list[int], None]:
            return State(lambda stack: (None, [value] + stack))

        def pop() -> State[list[int], int]:
            return State(lambda stack: (stack[0], stack[1:]) if stack else (0, []))

        def add() -> State[list[int], None]:
            return pop().bind(lambda x: pop().bind(lambda y: push(x + y)))

        def multiply() -> State[list[int], None]:
            return pop().bind(lambda x: pop().bind(lambda y: push(x * y)))

        # Create a program: calculate (3 + 4) * 2
        program = (
            push(2)
            .bind(lambda _: push(4))
            .bind(lambda _: push(3))
            .bind(lambda _: add())
            .bind(lambda _: multiply())
            .bind(lambda _: pop())
        )

        result, final_stack = program.run([])
        assert result == FOURTEEN  # (3 + 4) * 2 = 14
        assert final_stack == []  # Stack should be empty after all operations

    def test_game_state_management(self):
        """Test using State for game state management."""
        from dataclasses import dataclass

        # Define a game state type
        @dataclass
        class GameState:
            player_position: tuple[int, int]
            score: int
            inventory: list[str]
            game_time: int

        # Define game actions
        def move(dx: int, dy: int) -> State[GameState, None]:
            return State(
                lambda gs: (
                    None,
                    GameState(
                        player_position=(
                            gs.player_position[0] + dx,
                            gs.player_position[1] + dy,
                        ),
                        score=gs.score,
                        inventory=gs.inventory,
                        game_time=gs.game_time + 1,
                    ),
                )
            )

        def collect_item(item: str, points: int) -> State[GameState, bool]:
            return State(
                lambda gs: (
                    True,  # Success
                    GameState(
                        player_position=gs.player_position,
                        score=gs.score + points,
                        inventory=gs.inventory + [item],
                        game_time=gs.game_time + 1,
                    ),
                )
            )

        # Create a game sequence
        game_sequence = (
            move(0, 5)
            .bind(lambda _: collect_item("key", 10))
            .bind(lambda _: move(3, 2))
            .bind(lambda _: collect_item("treasure", 50))
            .bind(lambda _: move(-1, -2))
        )

        initial_game_state = GameState(
            player_position=(0, 0), score=0, inventory=[], game_time=0
        )

        _, final_game_state = game_sequence.run(initial_game_state)

        assert final_game_state.player_position == (2, 5)
        assert final_game_state.score == SIXTY  # 10 + 50
        assert final_game_state.inventory == ["key", "treasure"]
        assert final_game_state.game_time == FIVE  # One tick per action
