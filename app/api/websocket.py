from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import uuid
from datetime import datetime
import logging
from app.core.rag_engine import rag_engine

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket) -> str:
        """Connect a new WebSocket client"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Disconnect a WebSocket client"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
    
    async def send_message(self, connection_id: str, message: str):
        """Send a message to a specific client"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Send a message to all connected clients"""
        for connection_id, websocket in self.active_connections.items():
            await websocket.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """WebSocket endpoint for real-time queries"""
    connection_id = await manager.connect(websocket)
    try:
        while True:
            # Receive query from client
            data = await websocket.receive_text()
            try:
                # Parse the query
                query_data = json.loads(data)
                document_id = query_data.get("document_id")
                question = query_data.get("question")
                
                if not document_id or not question:
                    await manager.send_message(
                        connection_id, 
                        json.dumps({
                            "error": "Invalid query format. Please provide document_id and question."
                        })
                    )
                    continue
                
                # Send acknowledgement
                await manager.send_message(
                    connection_id,
                    json.dumps({
                        "type": "ack",
                        "query_id": str(uuid.uuid4()),
                        "timestamp": datetime.now().isoformat()
                    })
                )
                
                # Process the query with streaming
                async for token, _ in rag_engine.process_query_stream(document_id, question):
                    await manager.send_message(
                        connection_id,
                        json.dumps({
                            "type": "token",
                            "content": token
                        })
                    )
                
                # Send completion message
                await manager.send_message(
                    connection_id,
                    json.dumps({
                        "type": "complete",
                        "timestamp": datetime.now().isoformat()
                    })
                )
            
            except json.JSONDecodeError:
                await manager.send_message(
                    connection_id, 
                    json.dumps({
                        "error": "Invalid JSON format."
                    })
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket query: {e}", exc_info=True)
                await manager.send_message(
                    connection_id,
                    json.dumps({
                        "error": f"Error processing query: {str(e)}"
                    })
                )
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Client disconnected: {connection_id}")