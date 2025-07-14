# CodePush MCP Client API

This project provides a FastAPI-based HTTP API for managing and interacting with CodePush MCP sessions. It acts as a bridge between HTTP clients and the underlying MCP server, enabling session management, query processing, and tool usage via a simple REST interface.

## Features

- **Session Management:** Start and end CodePush MCP sessions using your access key.
- **Query Processing:** Send queries to the MCP server and receive responses, including tool usage.
- **Server Automation:** Automatically clones and sets up the MCP server repository and environment as needed.
- **Bedrock Integration:** Uses AWS Bedrock for LLM-powered query processing.

---

## Project Structure

```
codepush_mcp_api/
│
├── main.py                # FastAPI app entry point
├── pyproject.toml         # Project dependencies and metadata
├── src/
│   ├── controllers.py     # API endpoints and session logic
│   ├── mcp_server.py      # MCP server setup and environment management
│   ├── mcp_client.py      # Client logic for connecting to and interacting with MCP server
│   ├── schemas.py         # Data models and schemas
│   └── __init__.py
└── codepush_mcp/          # (Cloned MCP server repo will appear here)
```

---

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (for dependency and virtual environment management)
- [git](https://git-scm.com/)
- AWS credentials (for Bedrock access)
- A valid CodePush access key

---

## Installation & Setup

1. **Clone this repository:**
   ```sh
   git clone <this-repo-url>
   cd codepush_mcp_api
   ```

2. **Install `uv` if you don’t have it:**
   ```sh
   pip install uv
   ```

3. **Create and sync the virtual environment:**
   ```sh
   uv venv
   uv sync
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env` in the root directory.
   - Add your AWS and any other required credentials.

---

## Running the API

Start the FastAPI server using:

```sh
uv run python uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

---

## API Endpoints

### 1. Start a Session

- **POST** `/session/start`
- **Body:**
  ```json
  {
    "codepush_access_key": "YOUR_ACCESS_KEY"
  }
  ```
- **Response:**
  ```json
  {
    "session_id": "uuid-string",
    "status": "connected"
  }
  ```

### 2. End a Session

- **POST** `/session/end`
- **Query Parameter:** `session_id`
- **Response:**
  ```json
  { "status": "session ended" }
  ```

### 3. Process a Query

- **POST** `/query`
- **Body:**
  ```json
  {
    "session_id": "uuid-string",
    "query": "Your question or command"
  }
  ```
- **Response:**
  ```json
  {
    "messages": [ ... ]
  }
  ```

---

## How Sessions Work

- When you start a session, a new `MCPClient` is created and connected to the MCP server using your access key.
- Each session is identified by a unique UUID (`session_id`).
- All queries and tool usage are routed through the session context.
- When you end a session, the connection is cleaned up and removed from the active sessions list.
- Sessions are managed in-memory (see `active_sessions` in `src/controllers.py`).

---

## How the MCP Server is Managed

- On startup, the API checks for prerequisites (`git`, `uv`).
- If the MCP server repo (`codepush_mcp/`) is missing, it is cloned automatically.
- The environment is set up using `uv venv` and `uv sync` inside the cloned repo.
- The MCP server is started as a subprocess when a session is created.

---

## Testing the Endpoints

You can use `curl`, Postman, or any HTTP client. Here’s an example using `curl`:

**Start a session:**
```sh
curl -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{"codepush_access_key": "YOUR_ACCESS_KEY"}'
```

**Process a query:**
```sh
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "query": "Hello"}'
```

**End a session:**
```sh
curl -X POST "http://localhost:8000/session/end?session_id=YOUR_SESSION_ID"
```

**List active sessions:**
```sh
curl http://localhost:8000/sessions
```

---

## Notes

- The API is stateless except for in-memory session management. If the server restarts, all sessions are lost.
- The MCP server and client logic are tightly coupled; ensure the MCP server repo is accessible and up-to-date.
- For production, consider persistent session storage and secure handling of access keys.

---

