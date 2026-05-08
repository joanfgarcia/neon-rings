"""
Neon-Rings Server (Hub)
=======================
A lightweight WebSocket router and DHT storage for the Red-Pill ecosystem.
"""

import asyncio
import json
import logging
import sqlite3
import argparse
import time
from typing import Any, Dict, Optional, Set

import websockets

from .crypto import verify_signature

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("neon_rings.server")

class RingsServer:
    def __init__(self, db_path: str = ":memory:", host: str = "0.0.0.0", port: int = 50000):
        self.db_path = db_path
        self.host = host
        self.port = port
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.active_connections: Set[websockets.ServerConnection] = set()
        
        # In-memory mapping from node_id to websocket
        self.node_to_ws: Dict[str, websockets.ServerConnection] = {}
        # Reverse mapping for cleanup
        self.ws_to_node: Dict[websockets.ServerConnection, str] = {}
        
        self._init_db()

    def _init_db(self):
        with self.db:
            self.db.execute("CREATE TABLE IF NOT EXISTS dht (key TEXT PRIMARY KEY, value TEXT, updated_at REAL)")

    async def start(self):
        # websockets.serve automatically sends ping/pong frames
        async with websockets.serve(self.handle_client, self.host, self.port, ping_interval=20, ping_timeout=20):
            logger.info(f"Rings Server started on ws://{self.host}:{self.port} (DB: {self.db_path})")
            await asyncio.Future()  # run forever

    async def handle_client(self, websocket: websockets.ServerConnection):
        self.active_connections.add(websocket)
        logger.debug(f"New connection: {websocket.remote_address}")
        try:
            async for message in websocket:
                try:
                    req = json.loads(message)
                    response = await self.process_rpc(req, websocket)
                    if response:
                        await websocket.send(json.dumps(response))
                except Exception as e:
                    logger.error(f"Error handling message: {e}", exc_info=True)
                    try:
                        req_id = req.get("id") if isinstance(req, dict) else None
                        await websocket.send(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": req_id}))
                    except:
                        pass
        finally:
            self.active_connections.remove(websocket)
            node_id = self.ws_to_node.get(websocket)
            if node_id:
                logger.info(f"Node disconnected: {node_id}")
                self.node_to_ws.pop(node_id, None)
                self.ws_to_node.pop(websocket, None)

    async def process_rpc(self, req: Dict[str, Any], websocket: websockets.ServerConnection) -> Optional[Dict[str, Any]]:
        method = req.get("method")
        params = req.get("params", {})
        req_id = req.get("id")
        
        handler = getattr(self, f"handle_{method}", None)
        if not handler:
            return {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}, "id": req_id}
            
        try:
            result = await handler(params, websocket)
            if result is not None:
                return {"jsonrpc": "2.0", "result": result, "id": req_id}
        except Exception as e:
            logger.error(f"RPC Handler Error ({method}): {e}")
            return {"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": req_id}

    # -- Core RPC Methods --

    async def handle_register(self, params, websocket):
        node_id = params.get("node_id")
        if not node_id:
            raise ValueError("Missing node_id")
            
        self.node_to_ws[node_id] = websocket
        self.ws_to_node[websocket] = node_id
        logger.info(f"Node registered: {node_id}")
        return {"ok": True, "node_id": node_id}

    async def handle_send_message(self, params, websocket):
        target_id = params.get("target_id")
        payload = params.get("payload")
        
        sender_id = self.ws_to_node.get(websocket, "unknown")
        
        target_ws = self.node_to_ws.get(target_id)
        if target_ws:
            # Unsolicited notification to target
            notification = {
                "jsonrpc": "2.0",
                "method": "message_receive",
                "params": {"sender_id": sender_id, "payload": payload, "ts": time.time()}
            }
            await target_ws.send(json.dumps(notification))
            return {"ok": True, "delivered": True}
        else:
            # Not connected locally. If we add federation, we forward it here.
            return {"ok": True, "delivered": False, "reason": "Node offline"}

    async def handle_dht_put(self, params, websocket):
        key = params.get("key")
        value = params.get("value")
        signature_hex = params.get("signature")
        
        if not key or not value or not signature_hex:
            raise ValueError("Missing key, value, or signature")
            
        # Cryptographic verification
        try:
            signature = bytes.fromhex(signature_hex)
        except ValueError:
            raise ValueError("Invalid signature format")
            
        if not verify_signature(key, value.encode("utf-8"), signature):
            raise ValueError("Invalid cryptographic signature for DHT record")
            
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO dht (key, value, updated_at) VALUES (?, ?, ?)", (key, value, time.time()))
            
        return {"ok": True}

    async def handle_dht_get(self, params, websocket):
        cursor = self.db.execute("SELECT value FROM dht WHERE key = ?", (params["key"],))
        row = cursor.fetchone()
        return row[0] if row else None


def main():
    parser = argparse.ArgumentParser(description="Neon-Rings Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=50000, help="Port to bind to (default: 50000)")
    parser.add_argument("--db", type=str, default=":memory:", help="SQLite database path (default: in-memory)")
    
    args = parser.parse_args()
    
    server = RingsServer(db_path=args.db, host=args.host, port=args.port)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped manually.")

if __name__ == "__main__":
    main()
