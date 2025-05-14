from monawhat.maybe import Maybe, Just, Nothing  # noqa: D100

THE_RESPONSE = 42


class TestMaybe:
    """Tests for the Maybe monad base class and factory methods."""

    def test_factory_methods(self):
        """Test the factory methods create the correct types."""
        nothing = Maybe.nothing()
        just = Maybe.just(42)

        assert isinstance(nothing, Nothing)
        assert isinstance(just, Just)
        assert just.get() == THE_RESPONSE


class TestJust:
    """Tests for the Just case of the Option monad."""

    def test_is_just_nothing(self):
        """Test the type checking methods."""
        just = Just(42)

        assert just.is_just() is True
        assert just.is_nothing() is False

    def test_map(self):
        """Test map transforms the value for Just."""
        just = Just(21)
        result = just.map(lambda x: x * 2)

        assert result.is_just()
        assert result.get() == THE_RESPONSE

    def test_bind(self):
        """Test bind applies a function that returns an Option."""
        just = Just(21)

        # Test binding to a Just
        result1 = just.bind(lambda x: Just(x * 2))
        assert result1.is_just()
        assert result1.get() == THE_RESPONSE

        # Test binding to a Nothing
        result2 = just.bind(lambda x: Nothing())
        assert result2.is_nothing()

    def test_get(self):
        """Test get returns the wrapped value."""
        value = 42
        just = Just(value)

        assert just.get() == value

    def test_get_or_else(self):
        """Test get_or_else returns the wrapped value, ignoring default."""
        value = 42
        just = Just(value)

        assert just.get_or_else(100) == value

    def test_representation(self):
        """Test the string representation."""
        just = Just(42)

        assert repr(just) == "Just(42)"


class TestNothing:
    """Tests for the Nothing case of the Option monad."""

    def test_is_just_nothing(self):
        """Test the type checking methods."""
        nothing = Nothing()

        assert nothing.is_just() is False
        assert nothing.is_nothing() is True

    def test_map(self):
        """Test that map is ignored for Nothing."""
        nothing = Nothing()
        result = nothing.map(lambda x: x * 2)

        assert result.is_nothing()

    def test_bind(self):
        """Test that bind is ignored for Nothing."""
        nothing = Nothing()
        result = nothing.bind(lambda x: Just(x * 2))

        assert result.is_nothing()

    def test_get(self):
        """Test get raises an error for Nothing."""
        nothing = Nothing()

        try:
            nothing.get()
            assert False, "Expected ValueError to be raised"
        except ValueError:
            pass

    def test_get_or_else(self):
        """Test get_or_else returns the default value."""
        nothing = Nothing()
        default_value = THE_RESPONSE

        assert nothing.get_or_else(default_value) == default_value

    def test_representation(self):
        """Test the string representation."""
        nothing = Nothing()

        assert repr(nothing) == "Nothing()"


class TestPracticalUsage:
    """Tests demonstrating practical usage of the Option monad."""

    def test_find_example(self):
        """Test Option for finding an element in a collection."""

        def find_user_by_id(user_id, users):
            for user in users:
                if user["id"] == user_id:
                    return Maybe.just(user)
            return Maybe.nothing()

        users = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]

        # Successful find
        result1 = find_user_by_id(2, users)
        assert result1.is_just()
        assert result1.get()["name"] == "Bob"

        # User not found
        result2 = find_user_by_id(4, users)
        assert result2.is_nothing()
        assert result2.get_or_else({"name": "Guest"})["name"] == "Guest"

    def test_chain_operations(self):
        """Test chaining multiple operations using the Option monad."""

        def get_user(user_id):
            users = {1: "Alice", 2: "Bob", 3: "Charlie"}
            return (
                Maybe.just(users.get(user_id)) if user_id in users else Maybe.nothing()
            )

        def get_address(user):
            addresses = {"Alice": "123 Main St", "Bob": "456 Oak Ave"}
            return (
                Maybe.just(addresses.get(user))
                if user in addresses
                else Maybe.nothing()
            )

        def parse_zip_code(address):
            # Simple example: extract zip code if it ends with a 5-digit number
            import re

            match = re.search(r"(\d{5})$", address)
            return Maybe.just(match.group(1)) if match else Maybe.nothing()

        # Success case: chain all operations successfully
        result1 = Maybe.just(2).bind(get_user).bind(get_address)
        assert result1.is_just()
        assert result1.get() == "456 Oak Ave"

        # Failure at first step: user not found
        result2 = Maybe.just(4).bind(get_user).bind(get_address)
        assert result2.is_nothing()

        # Failure at second step: address not found
        result3 = Maybe.just(3).bind(get_user).bind(get_address)
        assert result3.is_nothing()

        # Test with parsing the zip code
        # Let's modify the address to include a zip code
        addresses_with_zip = {"Bob": "456 Oak Ave, 12345"}

        def get_address_with_zip(user):
            return (
                Maybe.just(addresses_with_zip.get(user))
                if user in addresses_with_zip
                else Maybe.nothing()
            )

        result4 = (
            Maybe.just(2).bind(get_user).bind(get_address_with_zip).bind(parse_zip_code)
        )
        assert result4.is_just()
        assert result4.get() == "12345"
