from fastapi import UploadFile, File, FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import uuid
import os
import asyncio
from openai import AsyncOpenAI
from datetime import datetime

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
app.mount("/static/uploaded_images", StaticFiles(directory=UPLOAD_DIR), name="uploaded_images")

# Tool function: get_current_time
async def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# OpenAI streaming handler for openai>=1.0.0 (text only)
async def mcp_stream(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        yield "[ERROR] OPENAI_API_KEY not set."
        return
    client = AsyncOpenAI(api_key=api_key)
    messages = [{"role": "user", "content": prompt}]
    stream = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta.content else ""
        if delta:
            yield delta

@app.get("/stream")
async def stream(request: Request):
    prompt = request.query_params.get("prompt", "Hello")
    async def event_generator():
        async for chunk in mcp_stream(prompt):
            yield {"data": chunk}
    return EventSourceResponse(event_generator())

# Streaming endpoint with tool use
@app.get("/stream-tool")
async def stream_tool(request: Request):
    prompt = request.query_params.get("prompt", "Hello")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        async def error_gen():
            yield {"data": "[ERROR] OPENAI_API_KEY not set."}
        return EventSourceResponse(error_gen())
    client = AsyncOpenAI(api_key=api_key)
    # Tool definition for OpenAI
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Returns the current server time.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    ]
    messages = [{"role": "user", "content": prompt}]
    stream = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=tools,
        stream=True
    )
    async def event_generator():
        got_event = False
        async for chunk in stream:
            print("RAW OPENAI CHUNK:", chunk)
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                # Handle streamed content
                if hasattr(delta, "content") and delta.content:
                    got_event = True
                    yield {"data": delta.content}
                # Handle streamed tool calls
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    got_event = True
                    for tool_call in delta.tool_calls:
                        # Extract tool name from function
                                    function = getattr(tool_call, "function", None)
                                    if function and getattr(function, "name", None) == "get_current_time":
                                        current_time = await get_current_time()
                                        # Send tool result as a string under 'data' for SSE compatibility
                                        yield {"data": f"Tool result: get_current_time: {current_time}"}
        if not got_event:
            yield {"data": "[No response from OpenAI]"}
    return EventSourceResponse(event_generator())

@app.get("/")
def root():
    return {"message": "MCP Streamable HTTP Server is running."}
