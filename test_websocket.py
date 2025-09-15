#!/usr/bin/env python3
"""
Simple WebSocket test script for Render.com deployment
Run with: python test_websocket.py
"""

import asyncio
import websockets
import sys

async def test_websocket():
    uri = "wss://task-backend-ed5i.onrender.com/ws"
    
    try:
        print(f"🔗 Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Send a test message
            test_message = "Hello from test script!"
            print(f"📤 Sending: {test_message}")
            await websocket.send(test_message)
            
            # Wait for response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            print("✅ WebSocket test completed successfully!")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
    except websockets.exceptions.InvalidURI as e:
        print(f"❌ Invalid URI: {e}")
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket connection to Render.com backend...")
    asyncio.run(test_websocket())
