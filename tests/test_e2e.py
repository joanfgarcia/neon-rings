import asyncio
import pytest
from neon_rings.server import RingsServer
from neon_rings.client import RingsClient
from neon_rings.crypto import KeyPair

@pytest.fixture
async def test_server():
    server = RingsServer(host="127.0.0.1", port=50002)
    task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)
    yield server
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_crypto_signature():
    kp = KeyPair.generate()
    sig = kp.sign(b"hello")
    from neon_rings.crypto import verify_signature
    assert verify_signature(kp.public_key_hex, b"hello", sig)
    assert not verify_signature(kp.public_key_hex, b"wrong", sig)

@pytest.mark.asyncio
async def test_e2e_dht(test_server):
    async with await RingsClient.from_url("ws://127.0.0.1:50002") as client:
        kp = KeyPair.generate()
        
        # Valid Put
        res = await client.dht_put(kp, "secret-payload")
        assert res["ok"] is True
        
        # Get
        val = await client.dht_get(kp.public_key_hex)
        assert val == "secret-payload"

@pytest.mark.asyncio
async def test_e2e_messaging(test_server):
    alice_received = []
    def on_alice_msg(sender, payload):
        alice_received.append((sender, payload))
        
    async with await RingsClient.from_url("ws://127.0.0.1:50002") as alice, \
               await RingsClient.from_url("ws://127.0.0.1:50002") as bob:
        
        alice.set_message_handler(on_alice_msg)
        
        await alice.register("alice-id")
        await bob.register("bob-id")
        
        res = await bob.send_message("alice-id", "Hello Alice")
        assert res["delivered"] is True
        
        # Wait a moment for background task to pick up message
        await asyncio.sleep(0.1)
        
        assert len(alice_received) == 1
        assert alice_received[0][0] == "bob-id"
        assert alice_received[0][1] == "Hello Alice"
