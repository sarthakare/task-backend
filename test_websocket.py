import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection to the notification endpoint"""
    uri = "ws://localhost:8000/ws/notifications/22"
    
    try:
        print(f"🔌 Connecting to {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send a ping message
            await websocket.send("ping")
            print("📤 Sent ping message")
            
            # Wait for pong response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            # Keep connection alive for a few seconds
            await asyncio.sleep(5)
            print("✅ WebSocket test completed successfully!")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket connection...")
    asyncio.run(test_websocket())
