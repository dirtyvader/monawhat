"""Tests for the Reader monad."""

from monawhat.reader import Reader
from dataclasses import dataclass
from typing import TypeVar

THE_RESPONSE = 42
HALF_RESPONSE = THE_RESPONSE / 2
THIRTY = 30
T = TypeVar('T')

@dataclass
class Environment:
    """Test environment with various data types."""
    value: int
    name: str
    items: list[str]
    data: dict[str, int]


class TestReader:
    """Tests for the Reader monad base class and factory methods."""

    def test_factory_methods(self):
        """Test the factory methods create the correct types."""
        # Test pure
        pure_reader = Reader.pure(THE_RESPONSE)
        assert pure_reader.run({}) == THE_RESPONSE
        
        # Test ask
        env = {"key": "value"}
        ask_reader = Reader.ask()
        assert ask_reader.run(env) is env
        
        # Test asks
        asks_reader = Reader.asks(lambda e: e["key"])
        assert asks_reader.run(env) == "value"

    def test_run(self):
        """Test running a Reader with an environment."""
        reader = Reader(lambda env: env["value"] * 2)
        result = reader.run({"value": 21})
        assert result == THE_RESPONSE

    def test_map(self):
        """Test the map function transforms the result."""
        reader = Reader(lambda env: env.value)
        mapped = reader.map(lambda x: x * 2)
        
        env = Environment(value=21, name="test", items=[], data={})
        result = mapped.run(env)
        
        assert result == THE_RESPONSE

    def test_bind(self):
        """Test the bind function chains Readers together."""
        get_value = Reader(lambda env: env.value)
        
        def multiply(x: int) -> Reader[Environment, int]:
            return Reader(lambda env: x * 2)
        
        chained = get_value.bind(multiply)
        env = Environment(value=21, name="test", items=[], data={})
        
        assert chained.run(env) == THE_RESPONSE

    def test_local(self):
        """Test running a Reader with a modified environment."""
        reader = Reader(lambda env: env.value)
        
        # Create a local reader that doubles the value in the environment
        local_reader = reader.local(lambda env: Environment(
            value=env.value * 2,
            name=env.name,
            items=env.items, 
            data=env.data
        ))
        
        env = Environment(value=21, name="test", items=[], data={})
        result = local_reader.run(env)
        
        assert result == THE_RESPONSE
        # Original environment should be unchanged
        assert env.value == HALF_RESPONSE

    def test_representation(self):
        """Test the string representation."""
        reader = Reader(lambda env: env.value)
        assert "Reader(" in repr(reader)


class TestReaderComposition:
    """Tests for composing multiple Reader operations."""

    def test_chaining_operations(self):
        """Test chaining multiple Reader operations."""
        # Get username from environment
        get_username = Reader.asks(lambda env: env["username"])
        
        # Format the username
        def format_username(username: str) -> Reader[dict, str]:
            return Reader(lambda env: f"{username}@{env['domain']}")
        
        # Chain the operations
        get_email = get_username.bind(format_username)
        
        env = {"username": "user", "domain": "example.com"}
        email = get_email.run(env)
        
        assert email == "user@example.com"
    
    def test_multiple_environment_accesses(self):
        """Test a computation that accesses the environment multiple times."""
        # Create readers to access different parts of environment
        get_base_url = Reader.asks(lambda env: env["base_url"])
        get_endpoint = Reader.asks(lambda env: env["endpoint"])
        get_api_key = Reader.asks(lambda env: env["api_key"])
        
        # Combine them to build a complete URL by composing the readers
        def build_url():
            return get_base_url.bind(lambda base_url:
                get_endpoint.bind(lambda endpoint:
                    get_api_key.map(lambda api_key:
                        f"{base_url}/{endpoint}?api_key={api_key}"
                    )
                )
            )
        
        env = {
            "base_url": "https://api.example.com",
            "endpoint": "users",
            "api_key": "abc123"
        }
        
        url = build_url().run(env)
        assert url == "https://api.example.com/users?api_key=abc123"


class TestPracticalUsage:
    """Tests demonstrating practical usage of the Reader monad."""
    
    def test_dependency_injection(self):
        """Test using Reader for dependency injection."""
        @dataclass
        class Dependencies:
            logger: list[str]  # Mock logger that stores log messages
            database: dict[str, dict]  # Mock database
        
        # Function that logs a message
        def log_message(message: str) -> Reader[Dependencies, None]:
            return Reader(lambda deps: deps.logger.append(message))
        
        # Function that gets a user from the database
        def get_user(user_id: str) -> Reader[Dependencies, dict]:
            return Reader(lambda deps: deps.database.get(user_id, {}))
        
        # Function that logs a user access and returns the user
        def get_user_with_logging(user_id: str) -> Reader[Dependencies, dict]:
            return log_message(f"Accessing user {user_id}").bind(
                lambda _: get_user(user_id).bind(
                    lambda user: log_message(f"Found user: {user}").map(
                        lambda _: user
                    )
                )
            )
        
        # Set up dependencies
        deps = Dependencies(
            logger=[],
            database={"user1": {"name": "Alice", "role": "admin"}}
        )
        
        # Run the computation
        user = get_user_with_logging("user1").run(deps)
        
        assert user == {"name": "Alice", "role": "admin"}
        assert len(deps.logger) == 2  # noqa: PLR2004
        assert "Accessing user user1" in deps.logger[0]
        assert "Found user:" in deps.logger[1]
    
    def test_configuration_management(self):
        """Test using Reader for configuration management."""
        @dataclass
        class AppConfig:
            debug: bool
            base_url: str
            timeout: int
            max_retries: int
        
        # Read various config values
        is_debug = Reader.asks(lambda config: config.debug)
        get_timeout = Reader.asks(lambda config: config.timeout)
        
        # Configure HTTP client based on config
        def configure_client() -> Reader[AppConfig, dict]:
            # Now using the readers we defined earlier
            return Reader.asks(lambda config: {
                "url": config.base_url,
                "timeout": config.timeout,
                "retries": config.max_retries,
                "debug": config.debug
            })
        
        # Create a modified config where debug is always True
        def force_debug(r: Reader[AppConfig, dict]) -> Reader[AppConfig, dict]:
            return r.local(lambda config: AppConfig(
                debug=True,
                base_url=config.base_url,
                timeout=config.timeout,
                max_retries=config.max_retries
            ))
        
        config = AppConfig(
            debug=False,
            base_url="https://api.example.com",
            timeout=30,
            max_retries=3
        )
        
        # Get normal client config
        client_config = configure_client().run(config)
        assert client_config["debug"] is False
        assert client_config["timeout"] == THIRTY
        
        # Get debug client config
        debug_client_config = force_debug(configure_client()).run(config)
        assert debug_client_config["debug"] is True
        assert debug_client_config["timeout"] == THIRTY
        
        # Directly test the individual readers
        assert is_debug.run(config) is False
        assert get_timeout.run(config) == THIRTY
    
    def test_reader_transformation(self):
        """Test transforming one reader to another with map and bind."""
        env = {"value": 21}
        
        # Create a reader that doubles the value
        double_reader = Reader(lambda e: e["value"] * 2)
        
        # Map: Transform the result with a function
        plus_one = double_reader.map(lambda x: x + 1)
        minus_one = double_reader.map(lambda x: x - 1)
        
        assert double_reader.run(env) == THE_RESPONSE
        assert plus_one.run(env) == THE_RESPONSE + 1
        assert minus_one.run(env) == THE_RESPONSE - 1
        
        # Bind: Chain with another reader
        def add_context(result: int) -> Reader[dict, str]:
            return Reader(lambda e: f"The result is {result} (from {e['value']})")
        
        with_context = double_reader.bind(add_context)
        assert with_context.run(env) == f"The result is {THE_RESPONSE} (from 21)"