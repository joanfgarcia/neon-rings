# Neon-Rings

A purely Python, lightweight, P2P WebSocket-based transport layer for the Red-Pill ecosystem.

## CLI Usage

### Server (Bootstrap Node)
Run the bootstrap server with an in-memory SQLite database (for testing) or a file for persistence:

```bash
neon-rings-server --host 0.0.0.0 --port 50000 --db node.db
```

### Client CLI
You can test the server from the command line:

```bash
neon-rings-client --endpoint ws://127.0.0.1:50000 info
neon-rings-client put --key "greeting" --value "Hello Swarm!"
neon-rings-client get --key "greeting"
```

## Security & Encryption
**Important**: `neon-rings` is **100% dumb to payload content**. It does not perform end-to-end encryption by itself. In the Red-Pill architecture, `pure-mls` is used to encrypt payloads *before* they are sent via `neon-rings`.
