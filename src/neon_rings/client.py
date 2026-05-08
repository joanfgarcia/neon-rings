"""
Neon-Rings Core Client
======================
A lightweight WebSocket router client for the Red-Pill ecosystem.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from .crypto import KeyPair
from .transport import create_transport


class RingsTransport(Protocol):
	is_connected: bool

	async def connect(self, endpoint: str = "") -> None: ...
	async def disconnect(self) -> None: ...
	async def call(self, method: str, params: dict[str, Any]) -> Any: ...


logger = logging.getLogger(__name__)


class RingsClient:
	def __init__(self, url: str = "", transport: RingsTransport | None = None):
		if not transport:
			if not url:
				raise ValueError("Must provide either url or transport")
			self._transport = create_transport(url)
		else:
			self._transport = transport

		self._node_id: str | None = None
		self._on_message_callback: Callable[[str, Any], None | Awaitable[None]] | None = None
		self._listen_task: asyncio.Task | None = None

	@classmethod
	async def from_url(cls, url: str) -> "RingsClient":
		client = cls(url=url)
		await client.connect()
		return client

	async def connect(self):
		if not self._transport.is_connected:
			await self._transport.connect()
		self._listen_task = asyncio.create_task(self._listen_loop())

	async def disconnect(self):
		if self._listen_task:
			self._listen_task.cancel()
		if self._transport.is_connected:
			await self._transport.disconnect()

	async def __aenter__(self):
		await self.connect()
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		await self.disconnect()

	def set_message_handler(self, callback: Callable[[str, Any], None | Awaitable[None]]):
		"""Set a callback for incoming messages."""
		self._on_message_callback = callback

	async def register(self, node_id: str):
		"""Register this client's ID with the Hub server."""
		self._node_id = node_id
		return await self._transport.call("register", {"node_id": node_id})

	async def send_message(self, target_id: str, payload: Any):
		"""Send a payload to a target node through the Hub."""
		return await self._transport.call("send_message", {"target_id": target_id, "payload": payload})

	async def dht_put(self, keypair: KeyPair, value: str):
		"""Store a value in the DHT. Key is automatically derived from the public key."""
		pub_hex = keypair.public_key_hex
		signature = keypair.sign(value.encode("utf-8")).hex()
		return await self._transport.call("dht_put", {"key": pub_hex, "value": value, "signature": signature})

	async def dht_get(self, key: str):
		"""Retrieve a value from the DHT."""
		return await self._transport.call("dht_get", {"key": key})

	async def _listen_loop(self):
		"""Listen for unsolicited push events from the server."""
		try:
			while self._transport.is_connected:
				# Assuming transport has a receive_event method that blocks
				if hasattr(self._transport, "receive_event"):
					event = await self._transport.receive_event()
					method = event.get("method")
					params = event.get("params", {})

					if method == "message_receive":
						sender_id = params.get("sender_id")
						payload = params.get("payload")
						if self._on_message_callback:
							if asyncio.iscoroutinefunction(self._on_message_callback):
								await self._on_message_callback(sender_id, payload)
							else:
								self._on_message_callback(sender_id, payload)
				else:
					await asyncio.sleep(0.1)
		except asyncio.CancelledError:
			pass
		except Exception as e:
			logger.error(f"Error in listen loop: {e}")
