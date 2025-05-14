"""Tests for the Identity monad."""

from monawhat.identity import Identity

THE_RESPONSE = 42
HALF_RESPONSE = THE_RESPONSE / 2
THIRTY_ONE = 31


class TestIdentityBasics:
    """Tests for basic Identity monad operations."""

    def test_creation_and_get(self):
        """Test creating an Identity monad and getting its value."""
        identity = Identity(THE_RESPONSE)
        assert identity.get() == THE_RESPONSE

    def test_pure(self):
        """Test the pure factory method."""
        identity = Identity.pure(THE_RESPONSE)
        assert identity.get() == THE_RESPONSE
        assert isinstance(identity, Identity)

    def test_map(self):
        """Test mapping a function over an Identity."""
        identity = Identity(HALF_RESPONSE)
        mapped = identity.map(lambda x: x * 2)
        
        assert mapped.get() == THE_RESPONSE
        assert isinstance(mapped, Identity)
        
        # Original Identity should be unchanged
        assert identity.get() == HALF_RESPONSE

    def test_bind(self):
        """Test binding an Identity to a function."""
        identity = Identity(HALF_RESPONSE)
        
        def double(x):
            return Identity(x * 2)
        
        result = identity.bind(double)
        
        assert result.get() == THE_RESPONSE
        assert isinstance(result, Identity)
        
        # Original Identity should be unchanged
        assert identity.get() == HALF_RESPONSE

    def test_representation(self):
        """Test the string representation of Identity."""
        identity = Identity(THE_RESPONSE)
        assert repr(identity) == f"Identity({THE_RESPONSE})"


class TestIdentityChaining:
    """Tests for chaining multiple Identity operations."""

    def test_chained_maps(self):
        """Test chaining multiple map operations."""
        result = (Identity(10)
                  .map(lambda x: x + 5)   # 15
                  .map(lambda x: x * 2)   # 30
                  .map(lambda x: x + 12))  # Changed from +2 to +12 to get 42
        
        assert result.get() == THE_RESPONSE  # (10 + 5) * 2 + 12 = 42

    def test_chained_binds(self):
        """Test chaining multiple bind operations."""
        def add_five(x):
            return Identity(x + 5)
        
        def multiply_by_two(x):
            return Identity(x * 2)
        
        def add_twelve(x):  # Changed from add_two to add_twelve
            return Identity(x + 12)  # Changed from +2 to +12
        
        result = (Identity(10)
                  .bind(add_five)         # 15
                  .bind(multiply_by_two)  # 30
                  .bind(add_twelve))      # 42
        
        assert result.get() == THE_RESPONSE  # (10 + 5) * 2 + 12 = 42

    def test_mixed_operations(self):
        """Test mixing map and bind operations."""
        def multiply_by_two(x):
            return Identity(x * 2)
        
        result = (Identity(5)
                  .map(lambda x: x + 5)     # 10
                  .bind(multiply_by_two)    # 20
                  .map(lambda x: x + 22))   # Changed from +12 to +22 to get 42
        
        assert result.get() == THE_RESPONSE  # (5 + 5) * 2 + 22 = 42


class TestPracticalUsage:
    """Tests demonstrating practical usage of the Identity monad."""

    def test_as_simple_container(self):
        """Test using Identity as a simple container for a value."""
        def process_data(data):
            return (Identity(data)
                    .map(lambda x: x.strip())
                    .map(lambda x: x.upper())
                    .map(lambda x: f"Processed: {x}")
                    .get())
        
        result = process_data("  hello world  ")
        assert result == "Processed: HELLO WORLD"

    def test_with_complex_objects(self):
        """Test Identity with more complex objects."""
        person = {"name": "Alice", "age": 30}
        
        result = (Identity(person)
                  .map(lambda p: {**p, "age": p["age"] + 1})
                  .map(lambda p: {**p, "greeting": f"Hello, {p['name']}!"})
                  .get())
        
        assert result["age"] == THIRTY_ONE
        assert result["greeting"] == "Hello, Alice!"
        assert result["name"] == "Alice"

    def test_identity_laws(self):
        """Test that Identity satisfies the monad laws."""
        # 1. Left identity: return a >>= f ≡ f a
        value = 5
        
        def f(x):
            return Identity(x * 2)
        
        left_identity_1 = Identity.pure(value).bind(f)
        left_identity_2 = f(value)
        
        assert left_identity_1.get() == left_identity_2.get()
        
        # 2. Right identity: m >>= return ≡ m
        m = Identity(value)
        right_identity = m.bind(Identity.pure)
        
        assert right_identity.get() == m.get()
        
        # 3. Associativity: (m >>= f) >>= g ≡ m >>= (\x -> f x >>= g)
        def g(x):
            return Identity(x + 10)
        
        associativity_1 = m.bind(f).bind(g)
        
        def f_then_g(x):
            return f(x).bind(g)
        
        associativity_2 = m.bind(f_then_g)
        
        assert associativity_1.get() == associativity_2.get()