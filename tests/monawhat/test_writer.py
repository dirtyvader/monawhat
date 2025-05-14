"""Tests for the Writer monad."""

from monawhat.writer import Writer
from typing import TypeVar

THE_RESPONSE = 42
HALF_RESPONSE = THE_RESPONSE / 2
ONE_HUNDRED_AND_TWENTY = 120
LOG_LENGTH = 5
THREE = 3
BIG_VALUE = 1150
SECOND_LOG_LENGTH = 4

# Type variable for tests
T = TypeVar('T')


class TestWriterBasics:
    """Tests for the Writer monad basic operations."""

    def test_init_and_run(self):
        """Test the initialization and running of a Writer."""
        # Create a writer with a value and some output
        writer = Writer(THE_RESPONSE, ["log message"], lambda x, y: x + y)
        value, output = writer.run()
        
        assert value == THE_RESPONSE
        assert output == ["log message"]
    
    def test_value_output_accessors(self):
        """Test the value and output accessor methods."""
        writer = Writer(THE_RESPONSE, "output", lambda x, y: x + y)
        
        assert writer.value() == THE_RESPONSE
        assert writer.output() == "output"


class TestWriterFactoryMethods:
    """Tests for the Writer monad factory methods."""
    
    def test_pure(self):
        """Test the pure factory method."""
        # Create a writer with pure
        writer = Writer.pure(THE_RESPONSE, [], lambda x, y: x + y)
        value, output = writer.run()
        
        assert value == THE_RESPONSE
        assert output == []
    
    def test_tell(self):
        """Test the tell factory method."""
        # Create a writer with tell
        writer = Writer.tell(["log message"], lambda x, y: x + y)
        value, output = writer.run()
        
        assert value is None
        assert output == ["log message"]


class TestWriterTransformations:
    """Tests for Writer monad transformation methods."""
    
    def test_map(self):
        """Test mapping a function over a Writer."""
        writer = Writer(HALF_RESPONSE, ["initial"], lambda x, y: x + y)
        mapped = writer.map(lambda x: x * 2)
        
        value, output = mapped.run()
        assert value == THE_RESPONSE
        assert output == ["initial"]
    
    def test_bind(self):
        """Test binding a Writer to another function."""
        writer = Writer(HALF_RESPONSE, ["first step"], lambda x, y: x + y)
        
        def double_with_log(x):
            return Writer(x * 2, ["doubled"], lambda x, y: x + y)
        
        bound = writer.bind(double_with_log)
        value, output = bound.run()
        
        assert value == THE_RESPONSE
        assert output == ["first step", "doubled"]
    
    def test_chained_binds(self):
        """Test chaining multiple binds."""
        writer = Writer.pure(10, [], lambda x, y: x + y)
        
        def add_with_log(x, n):
            return Writer(x + n, [f"Added {n}"], lambda x, y: x + y)
        
        # Chain multiple operations
        result = (writer
                  .bind(lambda x: add_with_log(x, 10))
                  .bind(lambda x: add_with_log(x, 22)))
        
        value, logs = result.run()
        assert value == THE_RESPONSE
        assert logs == ["Added 10", "Added 22"]


class TestWriterSpecialOperations:
    """Tests for Writer-specific operations."""
    
    def test_listen(self):
        """Test the listen operation."""
        writer = Writer(THE_RESPONSE, ["log message"], lambda x, y: x + y)
        result = writer.listen()
        
        value, output = result.run()
        
        # value should now contain both the original value and the output
        assert value == (THE_RESPONSE, ["log message"])
        assert output == ["log message"]
    
    def test_pass_output(self):
        """Test the pass_output operation."""
        # Create a writer whose value is a function that transforms the output
        def transform_fn(logs):
            return [log.upper() for log in logs]
        writer = Writer(transform_fn, ["log", "message"], lambda x, y: x + y)
        
        result = writer.pass_output()
        value, output = result.run()
        
        assert output == ["LOG", "MESSAGE"]
        assert callable(value)  # The value is still the function
    
    def test_censor(self):
        """Test the censor operation."""
        writer = Writer(THE_RESPONSE, ["sensitive", "data"], lambda x, y: x + y)
        
        # Apply a censoring function to the output
        censored = writer.censor(lambda logs: ["[REDACTED]" if log == "sensitive" else log for log in logs])
        
        value, output = censored.run()
        assert value == THE_RESPONSE
        assert output == ["[REDACTED]", "data"]


class TestMonoidTypeDefinition:
    """Tests to verify that the Monoid protocol works correctly."""
    
    def test_list_as_monoid(self):
        """Test that lists work as monoids."""
        writer = Writer(THE_RESPONSE, ["log"], None)  # Default combine uses +
        value, output = writer.run()
        
        assert value == THE_RESPONSE
        assert output == ["log"]
    
    def test_string_as_monoid(self):
        """Test that strings work as monoids."""
        writer = Writer(THE_RESPONSE, "hello", None)  # Default combine uses +
        value, output = writer.run()
        
        assert value == THE_RESPONSE
        assert output == "hello"
    
    def test_custom_combine_function(self):
        """Test using a custom combine function."""
        # Define a custom combine function
        def combine_by_max(x: list[int], y: list[int]) -> list[int]:
            return [max(a, b) for a, b in zip(x, y)] if len(x) == len(y) else x + y
        
        writer1 = Writer(THE_RESPONSE, [1, 5, 3], combine_by_max)
        writer2 = Writer(THE_RESPONSE + 1, [2, 3, 7], combine_by_max)
        
        result = writer1.bind(lambda _: writer2)
        _, output = result.run()
        
        assert output == [2, 5, 7]  # Element-wise maximum


class TestPracticalUsage:
    """Tests demonstrating practical usage of the Writer monad."""
    
    def test_logging_during_calculation(self):
        """Test using Writer for logging during a calculation."""
        def factorial_with_logs(n):
            """Calculate factorial with logging of steps."""
            if n <= 1:
                return Writer(1, [f"Factorial of {n} is 1"], lambda x, y: x + y)
            else:
                return factorial_with_logs(n - 1).bind(
                    lambda prev: Writer(
                        n * prev, 
                        [f"Factorial of {n} is {n * prev}"],
                        lambda x, y: x + y
                    )
                )
        
        result = factorial_with_logs(5)
        value, logs = result.run()
        
        assert value == ONE_HUNDRED_AND_TWENTY
        assert len(logs) == LOG_LENGTH
        assert "Factorial of 5 is 120" in logs
    
    def test_collecting_statistics(self):
        """Test using Writer to collect statistics during processing."""
        # A simple function to process items and collect stats
        def process_item(item):
            """Process an item and collect statistics."""
            # No longer takes stats as a parameter - it gets stats from the Writer output
            if item % 2 == 0:
                return Writer(f"Processed {item}", {"even_count": 1}, lambda x, y: {
                    **x, 
                    **y,
                    "even_count": x.get("even_count", 0) + y.get("even_count", 0),
                    "odd_count": x.get("odd_count", 0) + y.get("odd_count", 0),
                })
            else:
                return Writer(f"Processed {item}", {"odd_count": 1}, lambda x, y: {
                    **x, 
                    **y,
                    "even_count": x.get("even_count", 0) + y.get("even_count", 0),
                    "odd_count": x.get("odd_count", 0) + y.get("odd_count", 0),
                })
        
        # Process a list of items
        def process_items(items):
            """Process multiple items, collecting stats along the way."""
            result = Writer.pure("Start", {}, lambda x, y: {
                **x, 
                **y,
                "even_count": x.get("even_count", 0) + y.get("even_count", 0),
                "odd_count": x.get("odd_count", 0) + y.get("odd_count", 0),
            })
            
            for item in items:
                result = result.bind(lambda _: process_item(item))
            
            return result
        
        result = process_items([1, 2, 3, 4, 5, 6])
        value, stats = result.run()
        
        assert value == "Processed 6"  # Last processed item
        assert stats["even_count"] == THREE
        assert stats["odd_count"] == THREE
    
    def test_transaction_tracking(self):
        """Test using Writer to track financial transactions."""
        # Function to handle a transaction
        def make_transaction(account_balance, transaction_amount):
            """Handle a financial transaction with logging."""
            new_balance = account_balance + transaction_amount
            
            if transaction_amount >= 0:
                log = [f"Deposit: ${transaction_amount}"]
            else:
                log = [f"Withdrawal: ${abs(transaction_amount)}"]
            
            return Writer(new_balance, log, lambda x, y: x + y)
        
        # Start with initial balance
        account = Writer.pure(1000, [], lambda x, y: x + y)
        
        # Perform series of transactions
        transactions = [
            lambda balance: make_transaction(balance, -200),  # Withdraw 200
            lambda balance: make_transaction(balance, 50),    # Deposit 50
            lambda balance: make_transaction(balance, -300),  # Withdraw 300
            lambda balance: make_transaction(balance, 600)    # Deposit 600
        ]
        
        # Apply all transactions
        for transaction in transactions:
            account = account.bind(transaction)
        
        final_balance, transaction_log = account.run()
        
        assert final_balance == BIG_VALUE
        assert len(transaction_log) == SECOND_LOG_LENGTH
        assert "Withdrawal: $200" in transaction_log
        assert "Deposit: $600" in transaction_log