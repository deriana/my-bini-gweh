import json
import os
import shutil
import asyncio
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


class MCPManager:
    """
    Manages connections to MCP (Model Context Protocol) servers via stdio.
    Converts tools to OpenAI format and handles tool execution.
    """

    def __init__(self, config_path: str = "mcp_servers.json"):
        self.config_path = config_path
        self.exit_stack: Optional[AsyncExitStack] = None
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_to_server: Dict[str, str] = {}
        self.openai_tools: List[Dict[str, Any]] = []

    def _load_server_configs(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.config_path):
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("mcpServers", data.get("mcp_servers", {}))
        except Exception as e:
            print(f"[MCP] Failed to parse {self.config_path}: {e}")
            return {}

    async def initialize(self):
        """Connect to configured MCP servers and discover available tools."""
        if not HAS_MCP:
            print("[MCP] Python 'mcp' package not installed. MCP tools disabled.")
            return

        server_configs = self._load_server_configs()
        if not server_configs:
            print("[MCP] No MCP servers configured in mcp_servers.json.")
            return

        self.exit_stack = AsyncExitStack()
        self.openai_tools = []
        self.tool_to_server = {}

        for server_name, cfg in server_configs.items():
            cmd = cfg.get("command")
            args = cfg.get("args", [])
            env = cfg.get("env")
            cwd = cfg.get("cwd")

            if not cmd:
                continue

            # Verify if command is available on system
            if not shutil.which(cmd):
                print(f"[MCP] Warning: Command '{cmd}' not found on PATH. Skipping server '{server_name}'.")
                continue

            try:
                print(f"[MCP] Connecting to server '{server_name}' ({cmd} {' '.join(args)})...")
                server_params = StdioServerParameters(
                    command=cmd,
                    args=args,
                    env=env,
                    cwd=cwd
                )
                read, write = await self.exit_stack.enter_async_context(stdio_client(server_params))
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()

                self.sessions[server_name] = session
                tool_list = await session.list_tools()

                for tool in tool_list.tools:
                    self.tool_to_server[tool.name] = server_name
                    properties = tool.inputSchema.get("properties", {}) if tool.inputSchema else {}
                    required = tool.inputSchema.get("required", []) if tool.inputSchema else []

                    # Convert to OpenAI function calling tool schema
                    self.openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or f"Tool provided by {server_name}",
                            "parameters": {
                                "type": "object",
                                "properties": properties,
                                "required": required
                            }
                        }
                    })
                print(f"[MCP] Successfully loaded {len(tool_list.tools)} tools from server '{server_name}'.")
            except Exception as e:
                print(f"[MCP] Error initializing server '{server_name}': {e}")

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Returns tools formatted for OpenAI / Ollama tool calling."""
        return self.openai_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Executes a tool on the appropriate MCP server and returns text result."""
        server_name = self.tool_to_server.get(tool_name)
        if not server_name or server_name not in self.sessions:
            return f"Error: Tool '{tool_name}' not registered in any active MCP server."

        session = self.sessions[server_name]
        try:
            print(f"[MCP] Calling tool '{tool_name}' on server '{server_name}' with args {arguments}...")
            result = await session.call_tool(tool_name, arguments=arguments)
            # Combine text content from tool call result
            output_parts = []
            for item in result.content:
                if hasattr(item, "text"):
                    output_parts.append(item.text)
                else:
                    output_parts.append(str(item))
            return "\n".join(output_parts) if output_parts else "Success (no text output)"
        except Exception as e:
            print(f"[MCP] Error executing tool '{tool_name}': {e}")
            return f"Error executing tool '{tool_name}': {str(e)}"

    async def close(self):
        """Cleanup MCP connections."""
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.sessions.clear()
            self.tool_to_server.clear()
