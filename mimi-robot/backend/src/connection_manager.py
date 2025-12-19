"""
Mimi Robot - Connection Manager
Manages WebSocket connections from multiple devices
"""

import logging
from typing import Dict, Optional
from fastapi import WebSocket

logger = logging.getLogger("mimi-connection")


class ConnectionManager:
    """Manages active WebSocket connections"""

    def __init__(self):
        # WebSocket -> device_id mapping
        self.active_connections: Dict[WebSocket, Optional[str]] = {}
        # device_id -> WebSocket mapping
        self.devices: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[websocket] = None
        logger.info(f"New connection accepted. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        device_id = self.active_connections.get(websocket)

        if websocket in self.active_connections:
            del self.active_connections[websocket]

        if device_id and device_id in self.devices:
            del self.devices[device_id]

        logger.info(f"Connection closed. Total: {len(self.active_connections)}")

    async def register_device(self, websocket: WebSocket, device_id: str):
        """Register a device with its WebSocket connection"""
        self.active_connections[websocket] = device_id
        self.devices[device_id] = websocket
        logger.info(f"Device registered: {device_id}")

    def get_websocket(self, device_id: str) -> Optional[WebSocket]:
        """Get WebSocket for a device"""
        return self.devices.get(device_id)

    def get_device_id(self, websocket: WebSocket) -> Optional[str]:
        """Get device ID for a WebSocket"""
        return self.active_connections.get(websocket)

    async def send_to_device(self, device_id: str, message: dict):
        """Send a message to a specific device"""
        websocket = self.devices.get(device_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {device_id}: {e}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected devices"""
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

    def get_connected_devices(self) -> list:
        """Get list of connected device IDs"""
        return list(self.devices.keys())

    def is_device_connected(self, device_id: str) -> bool:
        """Check if a device is connected"""
        return device_id in self.devices

    @property
    def connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
