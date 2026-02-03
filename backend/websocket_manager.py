"""
WebSocket Manager - Manages WebSocket connections
"""
from fastapi import WebSocket
from typing import List
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[dict] = []
    
    async def connect(self, websocket: WebSocket, user_id: int = None, username: str = None, already_accepted: bool = False):
        """Register WebSocket connection (call accept() in endpoint first to avoid RuntimeError)."""
        if not already_accepted:
            await websocket.accept()
        self.active_connections.append({
            "ws": websocket,
            "user_id": user_id,
            "username": username
        })
        # Broadcast online count
        online_users = self.get_online_users()
        await self.broadcast({
            "type": "online_users",
            "count": len(online_users),
            "users": online_users
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        for conn in self.active_connections:
            if conn["ws"] == websocket:
                self.active_connections.remove(conn)
                break

    async def disconnect_and_broadcast(self, websocket: WebSocket):
        """Remove connection and broadcast update"""
        self.disconnect(websocket)
        online_users = self.get_online_users()
        await self.broadcast({
            "type": "online_users",
            "count": len(online_users),
            "users": online_users
        })
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict, recipient_id: int = None):
        """Broadcast message to all connected clients or specific recipient"""
        disconnected = []
        for connection in self.active_connections:
            # If recipient_id is specified, only send to that user (and the sender, ideally, but sender gets it via API response usually? No, WS is better for consistency)
            # Actually, for private chat, we want to send to:
            # 1. The recipient
            # 2. The sender (so they see it in other tabs)
            # But here we don't know the sender easily unless passed.
            # Let's keep it simple: if recipient_id is set, send ONLY to that user.
            # The sender usually adds it to their UI optimistically or via API response.
            # BUT, if I have multiple tabs open, I want my other tabs to see what I sent.
            # So maybe we should broadcast to everyone but clients filter? No, privacy.
            
            # Better approach:
            # If recipient_id is provided, send to connections with that user_id.
            if recipient_id is not None:
                if connection["user_id"] == recipient_id:
                    try:
                        await connection["ws"].send_text(json.dumps(message))
                    except:
                        disconnected.append(connection["ws"])
            else:
                # Broadcast to all
                try:
                    await connection["ws"].send_text(json.dumps(message))
                except:
                    disconnected.append(connection["ws"])
        
        # Remove disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_to_users(self, message: dict, user_ids):
        """Broadcast message to a specific list/set of user IDs."""
        if not user_ids:
            return
        allowed_ids = set(user_ids)
        disconnected = []
        for connection in self.active_connections:
            if connection.get("user_id") in allowed_ids:
                try:
                    await connection["ws"].send_text(json.dumps(message))
                except:
                    disconnected.append(connection["ws"])
        for ws in disconnected:
            self.disconnect(ws)

    def get_online_users(self):
        """Get list of online users"""
        users = {}
        for conn in self.active_connections:
            if conn["user_id"] and conn["username"]:
                users[conn["user_id"]] = conn["username"]
        
        return [{"id": uid, "username": uname} for uid, uname in users.items()]

