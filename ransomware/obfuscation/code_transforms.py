#!/usr/bin/env python3
"""
Code transformation utilities for obfuscation.
Runtime transformations to make static analysis harder.
"""

import builtins
import functools
import random
import string
import sys
from typing import Any, Callable, Dict, List, Optional


class StringObfuscator:
    """
    Runtime string obfuscation using XOR and base64.
    """

    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            key = b"PainPainXOR"
        self.key = key

    def xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """XOR encrypt data with key."""
        return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

    def obfuscate_string(self, s: str) -> str:
        """
        Obfuscate a string for runtime decryption.
        Returns a Python expression that evaluates to the string.
        """
        import base64
        encoded = base64.b64encode(self.xor_encrypt(s.encode(), self.key)).decode()
        return f"__import__('base64').b64decode('{encoded}').decode()"

    def get_decrypt_function(self) -> str:
        """
        Get Python code for the decryption function.
        Can be embedded in obfuscated scripts.
        """
        key_str = str(list(self.key))
        return f'''
def _d(e):
    import base64
    k = bytes({key_str})
    return bytes([b ^ k[i % len(k)] for i, b in enumerate(base64.b64decode(e))]).decode()
'''


class ImportObfuscator:
    """
    Obfuscate import statements.
    """

    @staticmethod
    def obfuscated_import(module: str, name: Optional[str] = None) -> Any:
        """
        Import a module using __import__ dynamically.
        """
        if name is None:
            return __import__(module)
        return getattr(__import__(module, fromlist=[name]), name)

    @staticmethod
    def delayed_import(module: str, delay_range: tuple = (0.1, 0.5)) -> Any:
        """
        Import with random delay to evade sandbox fast analysis.
        """
        import time
        time.sleep(random.uniform(*delay_range))
        return __import__(module)


class FunctionWrapper:
    """
    Wrap functions with obfuscation layers.
    """

    @staticmethod
    def add_junk_calls(func: Callable) -> Callable:
        """
        Decorator: Add junk function calls before execution.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Execute junk operations
            _junk_1()
            _junk_2()

            result = func(*args, **kwargs)

            # More junk after
            _junk_3()

            return result
        return wrapper

    @staticmethod
    def indirect_call(func: Callable, *args, **kwargs) -> Any:
        """
        Call a function indirectly through getattr/locals.
        """
        func_name = func.__name__
        local_funcs = locals()

        # Walk through frames to find function
        frame = sys._getframe()
        while frame:
            if func_name in frame.f_locals:
                actual_func = frame.f_locals[func_name]
                return actual_func(*args, **kwargs)
            frame = frame.f_back

        # Fallback
        return func(*args, **kwargs)


def _junk_1():
    """No-op junk function."""
    x = 0
    for i in range(random.randint(5, 15)):
        x = (x + i) ^ (i * 3)
    return x & 1


def _junk_2():
    """No-op junk function with string operations."""
    s = "".join(random.choices(string.ascii_letters, k=10))
    h = hash(s)
    return h % 2


def _junk_3():
    """No-op junk function with list operations."""
    lst = [random.random() for _ in range(5)]
    lst.sort()
    return sum(lst) > 2.5


class ControlFlowObfuscation:
    """
    Control flow obfuscation techniques.
    """

    @staticmethod
    def switch_dispatch(cases: Dict[int, Callable], case: int, *args, **kwargs) -> Any:
        """
        Dispatch through a switch-like structure.
        """
        if case in cases:
            return cases[case](*args, **kwargs)
        return None

    @staticmethod
    def state_machine(funcs: List[Callable], initial_state: int = 0) -> Any:
        """
        Execute functions through a state machine.
        """
        state = initial_state
        result = None

        while state >= 0:
            if state < len(funcs):
                result = funcs[state]()
                state += 1
            else:
                state = -1

        return result

    @staticmethod
    def opaque_jump(condition_func: Callable, true_branch: Callable,
                    false_branch: Callable, *args, **kwargs) -> Any:
        """
        Jump to different branches based on opaque condition.
        """
        if condition_func():
            return true_branch(*args, **kwargs)
        else:
            return false_branch(*args, **kwargs)


class NameObfuscation:
    """
    Obfuscate variable and function names.
    """

    def __init__(self):
        self.name_map: Dict[str, str] = {}
        self.used_names: set = set()

    def generate_name(self, length: int = 12) -> str:
        """Generate random identifier."""
        while True:
            # Start with underscore to avoid conflicts
            name = "_" + "".join(random.choices(string.ascii_letters + string.digits, k=length))
            if name not in self.used_names:
                self.used_names.add(name)
                return name

    def obfuscate_name(self, original: str) -> str:
        """Get or create obfuscated name."""
        if original not in self.name_map:
            self.name_map[original] = self.generate_name()
        return self.name_map[original]

    def get_mapping(self) -> Dict[str, str]:
        """Get current name mapping."""
        return self.name_map.copy()


class ArithmeticObfuscation:
    """
    Obfuscate arithmetic operations.
    """

    @staticmethod
    def add_obfuscated(a: int, b: int) -> int:
        """
        Compute a + b using obfuscated operations.
        Uses: a + b = ~(~a - b)
        """
        return ~(~a - b)

    @staticmethod
    def sub_obfuscated(a: int, b: int) -> int:
        """
        Compute a - b using obfuscated operations.
        Uses: a - b = ~(~a + b)
        """
        return ~(~a + b)

    @staticmethod
    def mul_obfuscated(a: int, b: int) -> int:
        """
        Compute a * b using Russian peasant multiplication.
        """
        result = 0
        while b > 0:
            if b & 1:
                result = ArithmeticObfuscation.add_obfuscated(result, a)
            a <<= 1
            b >>= 1
        return result

    @staticmethod
    def xor_obfuscated(a: int, b: int) -> int:
        """
        Compute a ^ b using only NOT, AND, OR.
        Uses: a ^ b = (a | b) & ~(a & b)
        """
        return (a | b) & ~(a & b)


# Runtime obfuscation decorators
def obfuscated(func: Callable) -> Callable:
    """
    Decorator to apply multiple obfuscation techniques.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Add junk code
        _junk_1()
        _junk_2()

        # Call with timing variation
        import time
        time.sleep(random.uniform(0.001, 0.01))

        return func(*args, **kwargs)

    return wrapper


def conditional_execute(condition: Callable, func: Callable) -> Callable:
    """
    Only execute if condition passes (opaque predicate).
    """
    def wrapper(*args, **kwargs):
        if condition():
            return func(*args, **kwargs)
        return None
    return wrapper


if __name__ == "__main__":
    print("Code Obfuscation Demo")
    print("=" * 50)

    # String obfuscation demo
    obf = StringObfuscator()
    test_string = "sensitive_api_key_12345"
    obfuscated = obf.obfuscate_string(test_string)
    print(f"Original: {test_string}")
    print(f"Obfuscated expression: {obfuscated}")
    print(f"Evaluates to: {eval(obfuscated)}")

    print("\n" + "=" * 50)

    # Name obfuscation demo
    names = NameObfuscation()
    originals = ["encrypt_file", "decrypt_key", "c2_server_url", "ransom_amount"]
    for orig in originals:
        obf_name = names.obfuscate_name(orig)
        print(f"{orig} -> {obf_name}")

    print("\n" + "=" * 50)

    # Arithmetic obfuscation
    a, b = 42, 13
    print(f"Normal: {a} + {b} = {a + b}")
    print(f"Obfuscated: {a} + {b} = {ArithmeticObfuscation.add_obfuscated(a, b)}")
    print(f"Normal: {a} * {b} = {a * b}")
    print(f"Obfuscated: {a} * {b} = {ArithmeticObfuscation.mul_obfuscated(a, b)}")
