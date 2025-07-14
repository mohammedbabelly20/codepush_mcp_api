from fastapi import HTTPException
from pydantic import BaseModel
import uuid

from .mcp_client import MCPClient


# Store active sessions
active_sessions: dict[str, MCPClient] = {}


class SessionRequest(BaseModel):
    codepush_access_key: str


class QueryRequest(BaseModel):
    session_id: str
    query: str


class SessionResponse(BaseModel):
    session_id: str
    status: str


async def start_session(request: SessionRequest):
    """Start a new session with the given access_key"""
    try:
        session_id = str(uuid.uuid4())
        client = MCPClient(request.codepush_access_key)

        connected = await client.connect_to_server()
        if not connected:
            raise HTTPException(
                status_code=500, detail="Failed to connect to MCP server"
            )

        active_sessions[session_id] = client
        return SessionResponse(session_id=session_id, status="connected")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start session: {str(e)}"
        )


async def end_session(session_id: str):
    """End a session and cleanup the connection"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        client = active_sessions[session_id]
        await client.cleanup()
        del active_sessions[session_id]
        return {"status": "session ended"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


async def process_query(request: QueryRequest):
    """Process a query for a specific session"""
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        client = active_sessions[request.session_id]
        messages = await client.process_query(request.query)
        return {"messages": messages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_active_sessions():
    """Get list of active session IDs"""
    return {"active_sessions": list(active_sessions.keys())}
