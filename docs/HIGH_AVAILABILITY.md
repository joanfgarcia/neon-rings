# High Availability & Scaling (Neon-Rings)

`neon-rings-server` is designed to be lightweight, sovereign, and zero-configuration by default, using an embedded SQLite database. However, as your Swarm grows, you may want to deploy multiple nodes for resilience.

We reject heavy dependencies like Redis, PostgreSQL, or Kafka for the default deployment. If you wish to scale `neon-rings-server`, choose one of the following Sovereign-friendly approaches:

## 1. The Magic Way: LiteFS (Recommended)

[LiteFS](https://fly.io/docs/litefs/) is an open-source (Apache 2.0) distributed file system specifically built to replicate SQLite databases. 

**How it works:**
You run your `neon-rings-server` on multiple machines pointing to the LiteFS mount point. LiteFS intercepts all SQLite writes on the primary node and replicates them to all secondary nodes in milliseconds via a Gossip protocol.
- **Pros**: Zero code changes. 100% transparent. Extremely fast.
- **Cons**: Requires setting up the LiteFS daemon alongside the Python app.

## 2. The P2P Way: Federation (Upcoming)

This is the pure "Software" approach. Nodes are given a `--federate ws://other-node:50000` flag.
- When `Node A` receives a `dht_put`, it saves it to its local SQLite and forwards the payload to `Node B`.
- When `Aleth` (connected to `Node A`) sends a message to `Titanium` (connected to `Node B`), `Node A` sees that Titanium is not locally connected and broadcasts the message to the Federation Ring.
- **Pros**: Pure Python, zero external daemons. True decentralized P2P architecture.
- **Cons**: Eventual consistency. Requires handling split-brain scenarios if nodes disconnect.

## 3. The Enterprise Way: Bring Your Own DB

If you already manage heavy infrastructure and want to integrate `neon-rings` into it, you can fork `server.py` and replace the 5 lines of SQLite code with your preferred driver (e.g., Redis, PostgreSQL, MongoDB). 
The JSON-RPC handlers are completely decoupled from the storage layer.
