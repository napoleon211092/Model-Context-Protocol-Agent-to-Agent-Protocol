import asyncio
import os
import sys
import json
from contextlib import AsyncExitStack
from typing import Optional, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv
load_dotenv()

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "content"):
            return {"type": o.__class__.__name__, "content": o.content}
        return super().default(o)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001",
    temperature=0,
    max_retries=2,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

if len(sys.argv) < 2:
    print("Usage: python langchain_mcp_client.py <docker|path_to_server_script>")
    sys.exit(1)

server_script = sys.argv[1]
# Nếu truyền 'docker', chạy bằng docker run, còn lại thì chạy file Python như cũ
if server_script == "docker":
    # Bạn có thể tùy chỉnh image name/path workspace ở đây:
    DOCKER_IMAGE = "server-gemini-docker:latest"
    HOST_WORKSPACE = os.path.expanduser("/root/Model-Context-Protocol-Agent-to-Agent-Protocol/docker/mcp-server/workspace")  # Sửa lại cho phù hợp máy bạn
    CONTAINER_WORKSPACE = "/root/workspace"

    # Đảm bảo thư mục HOST_WORKSPACE tồn tại
    os.makedirs(HOST_WORKSPACE, exist_ok=True)
    
    server_params = StdioServerParameters(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-v", f"{HOST_WORKSPACE}:{CONTAINER_WORKSPACE}",
            DOCKER_IMAGE
        ],
    )
else:
    server_params = StdioServerParameters(
        command="python" if server_script.endswith(".py") else "node",
        args=[server_script],
    )

mcp_client = None

async def run_agent():
    global mcp_client
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_client = type("MCPClientHolder", (), {"session": session})()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llm, tools)
            print("MCP Client Started! Type 'quit' to exit.")
            while True:
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break
                response = await agent.ainvoke({"messages": query})
                try:
                    formatted = json.dumps(response, indent=2, cls=CustomEncoder)
                except Exception as e:
                    formatted = str(response)
                print("\nResponse:")
                print(formatted)
    return

if __name__ == "__main__":
    asyncio.run(run_agent())
