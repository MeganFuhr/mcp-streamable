from fastapi import UploadFile, File, FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import uuid
import os
import asyncio
from openai import AsyncOpenAI

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
app.mount("/static/uploaded_images", StaticFiles(directory=UPLOAD_DIR), name="uploaded_images")

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

@app.get("/")
def root():
    return {"message": "MCP Streamable HTTP Server is running."}
