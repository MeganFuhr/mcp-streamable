# MCP Streamable HTTP Server

This project implements a streamable HTTP Model Context Protocol (MCP) server using Python and FastAPI. The server exposes endpoints for streaming model inference results over HTTP, compatible with MCP clients.

## References
- MCP Protocol: https://github.com/modelcontextprotocol
- Python SDK: https://github.com/modelcontextprotocol/python-mcp
- Implementation Guide: https://modelcontextprotocol.io/llms-full.txt

## Features
- FastAPI-based HTTP server
- Streaming responses using Server-Sent Events (SSE)
- MCP-compatible model handler

## Setup & Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Run the server: `python main.py`
3. Test streaming endpoint: Use curl or a browser to connect to `/stream` endpoint

## Debugging
You can debug and run this MCP server directly in VS Code.

---

This file will be updated as you progress through the setup steps.
