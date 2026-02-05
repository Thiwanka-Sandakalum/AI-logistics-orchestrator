"""
JSON-RPC client for communicating with the Execution Server.
"""
import uuid
import httpx
from typing import Any, Dict

EXECUTION_SERVER_URL = "http://execution-server:8080/rpc"

class MCPClientError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(f"MCPClientError {code}: {message}")
        self.code = code
        self.data = data

class MCPClient:
    def __init__(self, url: str = EXECUTION_SERVER_URL):
        self.url = url

    async def call(self, method: str, params: Dict[str, Any]) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, json=payload)
            result = response.json()
            if "error" in result:
                raise MCPClientError(result["error"]["code"], result["error"]["message"], result["error"].get("data"))
            return result["result"]
