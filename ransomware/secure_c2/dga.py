#!/usr/bin/env python3
"""
Domain Generation Algorithm (DGA) for C2.
Generates domain names algorithmically.
"""

import datetime
import hashlib


class DGA:
    """
    Domain Generation Algorithm.
    Generates pseudo-random domains based on seed.
    """

    def __init__(self, seed: str = "painpain"):
        self.seed = seed

    def generate_domains(self, count: int = 100) -> list:
        """Generate list of domains."""
        domains = []
        date = datetime.datetime.now()

        for i in range(count):
            # Create domain based on date and seed
            data = f"{self.seed}{date.strftime('%Y%m%d')}{i}"
            hash_bytes = hashlib.md5(data.encode()).digest()

            # Generate domain name
            length = 8 + (hash_bytes[0] % 8)
            domain_name = ""
            for j in range(length):
                domain_name += chr(ord('a') + (hash_bytes[j] % 26))

            tlds = ['.com', '.net', '.org', '.info', '.biz']
            tld = tlds[hash_bytes[-1] % len(tlds)]

            domains.append(domain_name + tld)

        return domains


if __name__ == "__main__":
    dga = DGA()
    domains = dga.generate_domains(10)
    print("Generated domains:")
    for d in domains:
        print(f"  {d}")
