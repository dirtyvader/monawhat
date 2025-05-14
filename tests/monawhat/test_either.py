# import pytest  # noqa: D100
from monawhat.either import Either, Left, Right

THE_RESPONSE = 42

class TestEither:
    """Tests for the Either monad base class and factory methods."""

    def test_factory_methods(self):
        """Test the factory methods create the correct types."""
        left = Either.left("error")
        right = Either.right(42)
        
        assert isinstance(left, Left)
        assert isinstance(right, Right)
        assert left.get() == "error"
        assert right.get() == THE_RESPONSE


class TestLeft:
    """Tests for the Left case of the Either monad."""

    def test_is_left_right(self):
        """Test the type checking methods."""
        left = Left("error")
        
        assert left.is_left() is True
        assert left.is_right() is False
    
    def test_map(self):
        """Test that map is ignored for Left."""
        left = Left("error")
        result = left.map(lambda x: x * 2)
        
        assert result.is_left()
        assert result.get() == "error"
    
    def test_bind(self):
        """Test that bind is ignored for Left."""
        left = Left("error")
        result = left.bind(lambda x: Right(x * 2))
        
        assert result.is_left()
        assert result.get() == "error"
    
    def test_get(self):
        """Test get returns the wrapped value."""
        error_message = "Something went wrong"
        left = Left(error_message)
        
        assert left.get() == error_message
    
    def test_get_or_else(self):
        """Test get_or_else returns the default value."""
        left = Left("error")
        default_value = THE_RESPONSE
        
        assert left.get_or_else(default_value) == default_value
    
    def test_representation(self):
        """Test the string representation."""
        left = Left("error")
        
        assert repr(left) == "Left(error)"


class TestRight:
    """Tests for the Right case of the Either monad."""

    def test_is_left_right(self):
        """Test the type checking methods."""
        right = Right(42)
        
        assert right.is_left() is False
        assert right.is_right() is True
    
    def test_map(self):
        """Test map transforms the value for Right."""
        right = Right(21)
        result = right.map(lambda x: x * 2)
        
        assert result.is_right()
        assert result.get() == THE_RESPONSE
    
    def test_bind(self):
        """Test bind applies a function that returns an Either."""
        right = Right(21)
        
        # Test binding to a Right
        result1 = right.bind(lambda x: Right(x * 2))
        assert result1.is_right()
        assert result1.get() == THE_RESPONSE
        
        # Test binding to a Left
        result2 = right.bind(lambda x: Left("error"))
        assert result2.is_left()
        assert result2.get() == "error"
    
    def test_get(self):
        """Test get returns the wrapped value."""
        value = 42
        right = Right(value)
        
        assert right.get() == value
    
    def test_get_or_else(self):
        """Test get_or_else returns the wrapped value, ignoring default."""
        value = 42
        right = Right(value)
        
        assert right.get_or_else(100) == value
    
    def test_representation(self):
        """Test the string representation."""
        right = Right(42)
        
        assert repr(right) == "Right(42)"


class TestPracticalUsage:
    """Tests demonstrating practical usage of the Either monad."""
    
    def test_division_example(self):
        """Test Either for handling division, including division by zero."""
        def safe_divide(a, b):
            if b == 0:
                return Either.left(f"Cannot divide {a} by zero")
            return Either.right(a / b)
        
        # Successful division
        result1 = safe_divide(10, 2)
        assert result1.is_right()
        assert result1.get() == 5.0  # noqa: PLR2004
        
        # Division by zero
        result2 = safe_divide(10, 0)
        assert result2.is_left()
        assert "Cannot divide" in result2.get()
    
    def test_chain_operations(self):
        """Test chaining multiple operations using the Either monad."""
        def safe_sqrt(x):
            if x < 0:
                return Either.left(f"Cannot calculate square root of {x}")
            return Either.right(x ** 0.5)
        
        def safe_reciprocal(x):
            if x == 0:
                return Either.left("Cannot calculate reciprocal of zero")
            return Either.right(1 / x)
        
        # Chain operations with bind
        # Calculate 1/sqrt(x)
        
        # Success case: x = 4
        result1 = Either.right(4).bind(safe_sqrt).bind(safe_reciprocal)
        assert result1.is_right()
        assert round(result1.get(), 4) == 0.5  # 1/sqrt(4) = 1/2 = 0.5  # noqa: PLR2004
        
        # Failure at first step: x = -4
        result2 = Either.right(-4).bind(safe_sqrt).bind(safe_reciprocal)
        assert result2.is_left()
        assert "square root" in result2.get()
        
        # Failure at second step: sqrt(0) = 0, then 1/0 fails
        result3 = Either.right(0).bind(safe_sqrt).bind(safe_reciprocal)
        assert result3.is_left()
        assert "reciprocal of zero" in result3.get()

    def test_match_with_type_conversions(self):
        """Test that match works with functions that return different types."""
        result1 = Either.left("error").match(
            lambda err: f"Error: {err}",
            lambda val: val * 2
        )
        assert result1 == "Error: error"
        
        result2 = Either.right(21).match(
            lambda err: f"Error: {err}",
            lambda val: val * 2
        )
        assert result2 == THE_RESPONSE