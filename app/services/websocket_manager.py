from fastapi import WebSocket
from typing import Dict, List, Set
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a new WebSocket for a user"""
        # Note: websocket.accept() is called in the main endpoint, not here
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
        
        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "message": "Connected to notification service",
                "timestamp": datetime.now().isoformat()
            },
            websocket
        )
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a WebSocket for a user"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Remove user if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            
            logger.info(f"User {user_id} disconnected. Remaining connections: {len(self.active_connections.get(user_id, set()))}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
    
    async def send_notification_to_user(self, user_id: int, notification: dict):
        """Send a notification to all connections of a specific user"""
        if user_id not in self.active_connections:
            logger.info(f"User {user_id} not connected, notification will be stored in database")
            return
        
        message = {
            "type": "notification",
            "data": notification,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connections of the user
        disconnected_websockets = set()
        for websocket in self.active_connections[user_id]:
            try:
                await self.send_personal_message(message, websocket)
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}")
                disconnected_websockets.add(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self.disconnect(websocket, user_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected users"""
        message_data = {
            "type": "broadcast",
            "data": message,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected_websockets = set()
        
        for user_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await self.send_personal_message(message_data, websocket)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected_websockets.add((websocket, user_id))
        
        # Clean up disconnected websockets
        for websocket, user_id in disconnected_websockets:
            self.disconnect(websocket, user_id)
    
    def get_connected_users(self) -> List[int]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self, user_id: int) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

# Global instance
websocket_manager = WebSocketManager()
