import argparse
import asyncio
from .client import RingsClient
from .crypto import KeyPair

async def run_client(endpoint: str, command: str, value: str, key_hex: str):
    async with await RingsClient.from_url(endpoint) as client:
        if command == "put":
            # In a real app you'd load your private key from a file.
            # Here we just generate a fresh one for the demo.
            kp = KeyPair.generate()
            res = await client.dht_put(kp, value)
            print(f"Stored value. Key is: {kp.public_key_hex}")
        elif command == "get":
            val = await client.dht_get(key_hex)
            print(f"Retrieved {key_hex} = {val}")

def main():
    parser = argparse.ArgumentParser(description="Neon-Rings CLI Client")
    parser.add_argument("--endpoint", type=str, default="ws://127.0.0.1:50000", help="WebSocket endpoint")
    parser.add_argument("command", choices=["put", "get"], help="Command to execute")
    parser.add_argument("--value", type=str, default="", help="DHT Value to put")
    parser.add_argument("--key", type=str, default="", dest="key_hex", help="DHT Key to get (hex)")
    
    args = parser.parse_args()
    asyncio.run(run_client(args.endpoint, args.command, args.value, args.key_hex))

if __name__ == "__main__":
    main()
