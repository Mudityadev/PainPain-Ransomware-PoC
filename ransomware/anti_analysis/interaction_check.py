#!/usr/bin/env python3
"""
User interaction checks for sandbox evasion.
Verifies human presence through various interaction checks.
"""

import os
import random
import time
from typing import Callable, Optional


class InteractionChecker:
    """
    Verify human presence through interaction checks.
    Sandboxes typically don't have real user interaction.
    """

    def __init__(self):
        self.is_windows = os.name == 'nt'

    def check_mouse_movement(self, duration: int = 5, min_movements: int = 3) -> bool:
        """
        Check if mouse has moved significantly.
        Returns True if enough movement detected.
        """
        if not self.is_windows:
            return True  # Skip on non-Windows

        try:
            import ctypes

            user32 = ctypes.windll.user32

            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            movements = 0
            prev_x, prev_y = 0, 0

            start = time.time()
            while time.time() - start < duration:
                pt = POINT()
                user32.GetCursorPos(ctypes.byref(pt))

                # Check if moved significantly
                if abs(pt.x - prev_x) > 10 or abs(pt.y - prev_y) > 10:
                    movements += 1
                    if movements >= min_movements:
                        return True

                prev_x, prev_y = pt.x, pt.y
                time.sleep(0.1)

        except Exception:
            pass

        return False

    def check_key_press(self, duration: int = 5) -> bool:
        """
        Check if any key has been pressed.
        """
        if not self.is_windows:
            return True

        try:
            import ctypes

            user32 = ctypes.windll.user32

            # Check each key
            start = time.time()
            while time.time() - start < duration:
                # Check if any key is pressed
                for key_code in range(256):
                    if user32.GetAsyncKeyState(key_code) & 0x8000:
                        return True
                time.sleep(0.05)

        except Exception:
            pass

        return False

    def require_interaction(self,
                            check_mouse: bool = True,
                            check_keyboard: bool = True,
                            duration: int = 10) -> bool:
        """
        Require some form of user interaction to continue.
        Returns True if interaction detected.
        """
        print("Please move your mouse or press any key to continue...")

        checks = []
        if check_mouse:
            checks.append(self.check_mouse_movement)
        if check_keyboard:
            checks.append(self.check_key_press)

        for check in checks:
            if check(duration):
                return True

        return False

    def random_delay_with_interaction_check(self,
                                            min_delay: float = 2.0,
                                            max_delay: float = 10.0,
                                            require_interaction: bool = False) -> bool:
        """
        Sleep with random delay, optionally checking for interaction.
        """
        delay = random.uniform(min_delay, max_delay)

        if require_interaction:
            # Check for interaction during delay
            return self.check_mouse_movement(int(delay), min_movements=1)
        else:
            time.sleep(delay)
            return True


class ExecutionDelayer:
    """
    Delay execution with various techniques.
    """

    @staticmethod
    def sleep_with_timing_check(sleep_seconds: float = 5.0) -> bool:
        """
        Sleep and verify timing wasn't accelerated.
        Returns False if time was accelerated (sandbox detected).
        """
        start = time.perf_counter()
        time.sleep(sleep_seconds)
        elapsed = time.perf_counter() - start

        # Allow 20% margin
        return elapsed >= sleep_seconds * 0.8

    @staticmethod
    def heavy_computation_delay(iterations: int = 100_000_000) -> float:
        """
        Delay via CPU-intensive computation.
        Harder to accelerate than simple sleep.
        """
        start = time.perf_counter()

        # CPU-intensive but useless computation
        result = 0
        for i in range(iterations):
            result = (result + i * i) % 1000000007

        elapsed = time.perf_counter() - start
        return elapsed

    @staticmethod
    def memory_allocation_delay(size_mb: int = 500) -> bool:
        """
        Allocate and touch large memory region.
        Some sandboxes have limited memory.
        """
        try:
            # Allocate
            size_bytes = size_mb * 1024 * 1024
            data = bytearray(size_bytes)

            # Touch all pages
            for i in range(0, size_bytes, 4096):
                data[i] = 1

            del data
            return True

        except MemoryError:
            return False


def check_human_presence(timeout: int = 10) -> bool:
    """
    Quick check for human presence.
    """
    checker = InteractionChecker()
    return checker.check_mouse_movement(duration=timeout, min_movements=2)


if __name__ == "__main__":
    print("Interaction Checker Test")
    print("=" * 60)

    checker = InteractionChecker()

    print("\n[*] Checking for mouse movement (5 seconds)...")
    if checker.check_mouse_movement(duration=5):
        print("[+] Mouse movement detected!")
    else:
        print("[!] No mouse movement - possible sandbox")

    print("\n[*] Checking for key press (5 seconds)...")
    if checker.check_key_press(duration=5):
        print("[+] Key press detected!")
    else:
        print("[!] No key press - possible sandbox")

    print("\n[*] Testing timing check...")
    delayer = ExecutionDelayer()
    if delayer.sleep_with_timing_check(2.0):
        print("[+] Timing normal")
    else:
        print("[!] Timing accelerated - sandbox detected")

    print("\n[*] Testing computation delay...")
    elapsed = delayer.heavy_computation_delay(10_000_000)
    print(f"[*] Computation took {elapsed:.2f} seconds")
