from fastapi import UploadFile, File, FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import uuid
import os
import asyncio
from openai import AsyncAzureOpenAI
from datetime import datetime

# Load environment variables from .env file if it exists
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Tool function: get_current_time
async def get_current_time(ticketID=None):
    # Use ticketID as needed
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Azure OpenAI streaming handler (text only)
async def mcp_stream(prompt):
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not api_key or not azure_endpoint or not deployment:
        yield "[ERROR] Azure OpenAI environment variables not set."
        return
    client = AsyncAzureOpenAI(
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version="2023-05-15"
    )
    messages = [{"role": "user", "content": prompt}]
    stream = await client.chat.completions.create(
        model=deployment,
        messages=messages,
        stream=True
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta.content else ""
        if delta:
            yield delta

@app.get("/stream")
async def stream_azure(request: Request):
    prompt = request.query_params.get("prompt", "Hello")
    async def event_generator():
        async for chunk in mcp_stream(prompt):
            yield {"data": chunk}
    return EventSourceResponse(event_generator())

@app.get("/stream-tool")
async def stream_tool_azure(request: Request):
    prompt = request.query_params.get("prompt", "Hello")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not api_key or not azure_endpoint or not deployment:
        async def error_gen():
            yield {"data": "[ERROR] Azure OpenAI environment variables not set."}
        return EventSourceResponse(error_gen())
    client = AsyncAzureOpenAI(
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version="2023-05-15"
    )
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Returns the current server time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticketID": {"type": "string"}
                    },
                    "required": ["ticketID"]
                }
            }
        }
    ]
    messages = [
        {"role": "user", "content": prompt},
        {
            "role": "tool",
            "content": None,
            "tool_call_id": "call-1",
            "name": "get_current_time",
            "arguments": {"ticketID": ticket_id_value}
        }
    ]
    stream = await client.chat.completions.create(
        model=deployment,
        messages=messages,
        tools=tools,
        stream=True
    )
    async def event_generator():
        got_event = False
        async for chunk in stream:
            print("RAW AZURE CHUNK:", chunk)
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    got_event = True
                    yield {"data": delta.content}
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    got_event = True
                    for tool_call in delta.tool_calls:
                        function = getattr(tool_call, "function", None)
                        if function and getattr(function, "name", None) == "get_current_time":
                            args = getattr(function, "arguments", {})
                            ticket_id = args.get("ticketID")
                            current_time = await get_current_time(ticket_id)
                            yield {"data": f"Tool result: get_current_time: {current_time}"}
        if not got_event:
            yield {"data": "[No response from Azure OpenAI]"}
    return EventSourceResponse(event_generator())

@app.get("/")
def root():
    return {"message": "MCP Azure OpenAI HTTP Server is running."}
