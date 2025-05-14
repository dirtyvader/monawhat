# monawhat

A modern, fully type-hinted, and comprehensively tested monad library for Python 3.11+.

```python
from monawhat.maybe import Maybe
from monawhat.either import Either
from monawhat.io import IO

# Instead of:
try:
    user = get_user(user_id)
    if user is None:
        print("User not found")
    else:
        email = user.get("email")
        if email is None:
            print("Email not found")
        else:
            send_email(email, "Welcome!")
except Exception as e:
    log_error(e)

# Write:
result = (Either.right(user_id)                                      # 'lift' a value to the Either monad
          .bind(lambda id: safely_get_user(id))                      # 'bind' a function that returns another Either
          .bind(lambda user: Maybe.from_optional(user.get("email"))  # 'bind' a function that returns a Maybe, which is then lifted to an Either
                .to_either("Email not found"))
          .bind(lambda email: safely_send_email(email, "Welcome!"))) # 'bind' a function that returns an Either
          .match(                                                    # 'match' on the Either to decide what to do next
              left=lambda error: IO.print(f"Error: {error}"),        # left branch is an error, so we print the error message (using IO monad)
              right=lambda _: IO.print("Email sent!")                # right branch is a success, so we print a success message (using IO monad)
          )

result.run()
```

## Why monads in Python?

Monads provide a structured way to handle common programming patterns:

- **Composition** - Chain operations without deeply nested functions or complex error handling
- **Side effect isolation** - Make code more predictable and testable
- **Context propagation** - Carry additional information (like state or logs) through your computation
- **Error handling** - Process potential failures in a clean, functional way

They come from functional programming, where they are a core concept. While Python is not a purely functional language, these functional programming patterns can make your code more maintainable, testable, and robust.

## Functional purity
Purity is a core concept in functional programming. It means that a function should not have any side effects and should always return the same output for the same input. Python is not a pure functional language, but we can still use some of its features to write functional-style code.

## Why another monad Python package?

`monawhat` is different from other monad libraries:

- **Modern Python features** - Uses Python 3.11+ typing features and latest language patterns
- **Comprehensive type hints** - Full type safety with no `Any` cop-outs
- **Thoroughly tested** - ~~100%~~ 95% test coverage with clear examples
- **Educational design** - Built to be approachable with clear documentation
- **Actively maintained** - Supported until all planned features in `monawhat_extras` are complete (Or the hype for the lib is so huge that I can't seriously let it go)

`monawhat` focuses on being a fresh, modern implementation that feels at home in contemporary Python code.

## Installation

```bash
# Using pip
pip install monawhat

# Using uv (faster)
uv add monawhat
# or
uv pip install monawhat

# Using Poetry
poetry add monawhat

# Using Conda
conda install -c conda-forge monawhat
```

~~For advanced features, install the extras package:~~ (soon)

## Core Concepts

`monawhat` provides these core monads:

- **Maybe** - Handle optional values without null checks (`Just` or `Nothing`)
- **Either** - Handle success/failure cases explicitly (`Right` or `Left`)  
- **State** - Thread state through computations without mutating variables
- **Reader** - Access shared environment/configuration without global variables
- **Writer** - Accumulate logs or other output alongside computation
- **IO** - Make side effects explicit and composable
- **Identity** - Wrap a value without changing it. Useful for building more complex monads.

All monads extends the `BaseMonad` class, which provides a common interface for all monads:
- `pure`: Create a monad from a value
- `bind`: Chain operations together
- `map`: Apply a function to the value inside the monad

Aside of that, each monad has its own unique methods and properties. For e

## Examples: Vanilla Python vs Monads

### Maybe Monad: Handling Optional Values
`Maybe` have two variants: `Just` and `Nothing`. `Just` represents a value, while `Nothing` represents the absence of a value.
`Maybe` provides a safe way to handle optional values without null checks. Similar to `Optional` in Java or `Option` in Rust.

```python
# Vanilla Python
def get_user_city(user_id):
    user = find_user(user_id)
    if user is None:
        return None
    address = user.get("address")
    if address is None:
        return None
    return address.get("city")

# With Maybe Monad
from monawhat.maybe import Maybe

def get_user_city(user_id):
    return (Maybe.from_optional(find_user(user_id))
            .bind(lambda user: Maybe.from_optional(user.get("address")))
            .bind(lambda addr: Maybe.from_optional(addr.get("city"))))
```

### Either Monad: Error Handling
`Either` has two variants: `Right` and `Left`. `Right` represents a successful result, while `Left` represents an error. `Either` provides a way to handle errors explicitly. Similar to `Result` in Rust.

```python
# Vanilla Python
def divide_and_process(a, b):
    try:
        if b == 0:
            return f"Error: Division by zero"
        result = a / b
        if result < 0:
            return f"Error: Negative result {result}"
        return f"Success: {result ** 2}"
    except Exception as e:
        return f"Error: {str(e)}"

# With Either Monad
from monawhat.either import Either

def divide_safely(a, b):
    return Either.right(a / b) if b != 0 else Either.left("Division by zero")

def process_positive(x):
    return Either.right(x ** 2) if x >= 0 else Either.left(f"Negative result {x}")

def divide_and_process(a, b):
    return (divide_safely(a, b)
            .bind(process_positive)
            .match(
                left=lambda err: f"Error: {err}",
                right=lambda result: f"Success: {result}"
            ))
```

### State Monad: Managing State
`State` allows you to manage state without mutating variables. It embeds computations in a stateful context, allowing you to chain operations that depend on the current state. Of course, at the end, you can extract both the final state and the result.

`State` have run method that returns a tuple of the final state and the result. exec and eval methods respectively return the final state and the result.

```python
# Vanilla Python
def process_items(items):
    result = []
    counter = 0
    for item in items:
        counter += 1
        if item > 0:
            result.append(item * 2)
    return result, counter

# With State Monad
from monawhat.state import State

def process_items(items):
    def process_item(item):
        return State(lambda s: 
            (item * 2 if item > 0 else None, 
             {"count": s["count"] + 1, "results": s["results"] + ([item * 2] if item > 0 else [])})
        )
    
    state_monad = State.sequence([process_item(item) for item in items])
    final_state = state_monad.exec({"count": 0, "results": []})
    return final_state["results"], final_state["count"]
```

### IO Monad: Managing Side Effects
`IO` monad is somewhat special. It's not a pure monad, as it allows side effects. It's a monad that represents an effectful computation. It's useful for managing side effects like input/output, file operations, or network requests.

`IO` is the mandatory mechanism for I/O operations in Haskell language. Python have already good mechanisms for I/O, and it allow side effects everywhere, so `IO` is here for consistency.

It comes in two variants: `IO` and `IOLite`. `IOLite` is a minimal implementation focused on core monad operations. `IO` is a full-featured, still generalist, IO monad.

#### When to use IOLite:
- For simpler applications where basic composition is sufficient
- When introducing functional concepts to a team unfamiliar with monads
- When you want minimal overhead for IO abstractions

#### When to use the full IO:
- For complex applications with extensive IO operations
- When you need robust error handling in a functional style
- When working with many different IO sources (files, network, etc.)
- When testability and mocking are important

```python
# Vanilla Python
def get_user_info():
    try:
        name = input("Enter your name: ")
        age = int(input("Enter your age: "))
        print(f"Hello, {name}! You are {age} years old.")
        return name, age
    except ValueError:
        print("Invalid age entered")
        return None, None

# With IO Monad
from monawhat.io import IO

def get_user_info():
    return (
        IO.input("Enter your name: ")
        .bind(lambda name: 
            IO.input("Enter your age: ")
            .bind(lambda age_str: 
                IO.pure((name, int(age_str)))
                .bind(lambda pair: 
                    IO.print(f"Hello, {pair[0]}! You are {pair[1]} years old.")
                    .map(lambda _: pair)
                )
            )
            .catch(lambda _: 
                IO.print("Invalid age entered")
                .map(lambda _: (name, None))
            )
        )
    )
```

[More examples in the documentation →](#documentation)

## Educational Purpose

`monawhat` is designed as both an educational tool and a practical library:

- **Learn functional programming** concepts in a Python context
- **Understand monads** through clear, well-documented implementations
- **Explore category theory** via practical examples
- **Compare approaches** between imperative and functional styles

## Practical Advantages

Beyond education, `monawhat` offers real practical benefits:

- **Error handling** - Eliminate deeply nested try/except blocks
- **Code organization** - Cleaner data flow and more maintainable structure  
- **Testability** - Side effect isolation makes testing simpler
- **Composability** - Build complex operations from simple pieces
- **Type safety** - Leverage Python's type system more effectively

## Disclaimer: Monads in Python

Python is primarily an imperative, multi-paradigm language that already provides mechanisms for many problems that monads solve in purely functional languages:

- Python has mutable state, so `State` monad isn't strictly necessary
- Python has exceptions, so `Either` monad isn't required for error handling
- Python has `None` and the walrus operator (new in 3.8 `:=`), partially replacing `Maybe`

However, monads provide a more structured, composable approach that can improve code clarity, maintainability, and reasoning, even in Python.

## Documentation

[Full documentation website](https://monawhat.readthedocs.io/) (🚧 In progress)

- [Tutorial: Getting started](https://monawhat.readthedocs.io/tutorials/getting-started) (🚧 In progress)
- [Guide: Choosing the right monad](https://monawhat.readthedocs.io/guides/choosing-monads) (🚧 In progress)
- [API Reference](https://monawhat.readthedocs.io/api/reference) (🚧 In progress)
- [Examples collection](https://monawhat.readthedocs.io/examples) (🚧 In progress)

## About the Name

The name "monawhat" is intended to be read as "Mona...WHAT?!" – as in "What the f... is a monad?!"

This name acknowledges the initial confusion many developers experience when first encountering monads, especially in a language like Python where functional programming concepts aren't as common. The library aims to bridge this gap and make these powerful concepts more approachable.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Personal Note

I was helped by a Large Language Model to write this library, but the process enabled me to learn more about Python's type hint system and the world of monads and functional programming. This project combines my passion for clean code with exploration of functional programming concepts in a traditionally imperative language.

---

Contributions are welcome! Please feel free to submit a Pull Request.