import os
import subprocess
from mcp.server.fastmcp import FastMCP
import time
mcp = FastMCP("terminal_server_docker") # Tạo một MCP server với ID tên là terminal, dùng để đăng ký các tool và xử lý yêu cầu từ client.
DEFAULT_WORKSPACE = os.path.expanduser("/root/workspace")
# Các tools được gắn thêm bằng @mcp.tool().
@mcp.tool()
# Ham chay lenh shell
async def run_command_gemini(command: str) -> str:
    """
    Run a terminal command inside the workspace directory. 
    If a terminal command can accomplish a task, 
    tell the user you'll use this tool to accomplish it,
    even though you cannot directly do it

    Args:
        command: The shell command to run.
    
    Returns:
        The command output or an error message.
    """
    try:
        result = subprocess.run(command, shell=True, cwd=DEFAULT_WORKSPACE, capture_output=True, text=True)
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print("Running")
    mcp.run(transport='stdio')
    while True:
        time.sleep(60)