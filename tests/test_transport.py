import pytest
import asyncio
from neon_rings.transport import create_transport, MultiNodeTransport, HTTPTransport, WebSocketTransport

@pytest.mark.asyncio
async def test_create_transport():
    # Test HTTP
    t_http = create_transport("http://localhost:8080")
    assert isinstance(t_http, HTTPTransport)
    
    # Test WebSocket
    t_ws = create_transport("ws://localhost:50000")
    assert isinstance(t_ws, WebSocketTransport)
    
    # Test MultiNode
    t_multi = create_transport("ws://node1:50000,ws://node2:50000")
    assert isinstance(t_multi, MultiNodeTransport)
    assert len(t_multi._urls) == 2

@pytest.mark.asyncio
async def test_multinode_failover():
    t_multi = create_transport("ws://fake-node1:50000,ws://fake-node2:50000")
    
    # Neither exists, so connect should fail, but we can verify it attempts them
    try:
        await t_multi.connect("")
    except Exception:
        pass
        
    assert not t_multi.is_connected
    
    # Disconnect should be safe even if not connected
    await t_multi.disconnect()

@pytest.mark.asyncio
async def test_http_transport():
    t_http = HTTPTransport("http://fake-node:8080")
    
    await t_http.connect("")
    assert t_http.is_connected
    
    # Call should raise because fake-node doesn't exist
    with pytest.raises(Exception):
        await t_http.call("node_info", {})
        
    await t_http.disconnect()
    assert not t_http.is_connected
