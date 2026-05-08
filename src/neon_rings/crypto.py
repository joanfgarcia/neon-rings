import os
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class KeyPair:
    def __init__(self, private_key: ed25519.Ed25519PrivateKey):
        self._private_key = private_key
        self._public_key = private_key.public_key()

    @classmethod
    def generate(cls) -> "KeyPair":
        return cls(ed25519.Ed25519PrivateKey.generate())

    @property
    def public_key_hex(self) -> str:
        raw = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return raw.hex()

    def sign(self, data: bytes) -> bytes:
        return self._private_key.sign(data)

def verify_signature(public_key_hex: str, data: bytes, signature: bytes) -> bool:
    try:
        raw_pub = bytes.fromhex(public_key_hex)
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(raw_pub)
        pub_key.verify(signature, data)
        return True
    except Exception:
        return False
