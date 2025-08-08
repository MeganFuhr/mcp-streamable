async def mcp_stream(prompt):
    # Check for Azure OpenAI environment variables
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if azure_endpoint and azure_api_key and azure_deployment:
        client = AsyncOpenAI(
            api_key=azure_api_key,
            base_url=f"{azure_endpoint}/openai/deployments/{azure_deployment}",
            api_version="2023-05-15"  # Update to your Azure API version if needed
        )
        model = None  # Azure uses deployment, not model name
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            yield "[ERROR] OPENAI_API_KEY or Azure OpenAI credentials not set."
            return
        client = AsyncOpenAI(api_key=api_key)
        model = "gpt-3.5-turbo"

    messages = [{"role": "user", "content": prompt}]
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta.content else ""
        if delta:
            yield delta