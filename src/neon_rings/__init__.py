"""
Neon-Rings
==========
Sovereign P2P WebSocket router for the Red-Pill ecosystem.
"""

from .client import RingsClient
from .server import RingsServer
from .crypto import KeyPair, verify_signature

__version__ = "0.1.0-alpha.0"
__all__ = [
    "RingsClient",
    "RingsServer",
    "KeyPair",
    "verify_signature",
]
