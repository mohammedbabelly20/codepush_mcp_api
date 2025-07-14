from contextlib import asynccontextmanager

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn

from src.controllers import (
    active_sessions,
    start_session,
    end_session,
    process_query,
    get_active_sessions,
    SessionResponse,
)
from src.mcp_server import MCPServer


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MCPServer().setup():
        print("Failed to set up MCP server. Exiting.")
        raise SystemExit(1)
    yield

    # Cleanup all sessions on shutdown
    for _, client in active_sessions.items():
        await client.cleanup()
    active_sessions.clear()


app = FastAPI(title="CodePush MCP Client API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints
app.post("/session/start", response_model=SessionResponse)(start_session)
app.post("/session/end")(end_session)
app.post("/query")(process_query)
app.get("/sessions")(get_active_sessions)


async def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
