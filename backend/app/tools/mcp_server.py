import json
import sys
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.tools.mcp_tools import (
    get_due_items,
    fetch_level_vocab,
    log_error_tag,
    schedule_next_review,
    get_learner_profile,
    MCP_TOOL_DEFINITIONS
)

mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])

class MCPCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}

class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    method: str
    params: Optional[Dict[str, Any]] = None

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Dispatches a call to the underlying tool implementation."""
    if tool_name == "get_due_items":
        user_id = arguments.get("user_id")
        limit = arguments.get("limit", 10)
        items = get_due_items(user_id=user_id, limit=limit)
        return [i.model_dump() if hasattr(i, "model_dump") else (i.dict() if hasattr(i, "dict") else i) for i in items]

    elif tool_name == "fetch_level_vocab":
        level = arguments.get("level", "A1")
        theme = arguments.get("theme", "travel")
        k = arguments.get("k", 5)
        query_text = arguments.get("query_text")
        return fetch_level_vocab(level=level, theme=theme, k=k, query_text=query_text)

    elif tool_name == "log_error_tag":
        return log_error_tag(
            user_id=arguments.get("user_id"),
            vocab_item_id=arguments.get("vocab_item_id"),
            error_type=arguments.get("error_type", "other"),
            severity=arguments.get("severity", "medium"),
            example_turn=arguments.get("example_turn", ""),
            correction=arguments.get("correction"),
            explanation=arguments.get("explanation")
        )

    elif tool_name == "schedule_next_review":
        res = schedule_next_review(
            user_id=arguments.get("user_id"),
            vocab_item_id=arguments.get("vocab_item_id"),
            outcome=arguments.get("outcome", "correct")
        )
        return res.model_dump() if (res and hasattr(res, "model_dump")) else (res.dict() if (res and hasattr(res, "dict")) else res)

    elif tool_name == "get_learner_profile":
        return get_learner_profile(user_id=arguments.get("user_id"))

    else:
        raise ValueError(f"Unknown MCP tool '{tool_name}'")


@mcp_router.get("/tools")
def list_mcp_tools():
    """List available MCP tools and their schemas."""
    return {"tools": MCP_TOOL_DEFINITIONS}

@mcp_router.post("/call")
def call_mcp_tool_rest(req: MCPCallRequest):
    """Direct REST endpoint to execute an MCP tool."""
    try:
        result = dispatch_tool_call(req.name, req.arguments)
        return {"tool": req.name, "result": result, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "MCP_TOOL_ERROR", "message": str(e)}}
        )

@mcp_router.post("")
def handle_jsonrpc(req: JSONRPCRequest):
    """Standard JSON-RPC 2.0 MCP endpoint."""
    if req.method in ["tools/list", "list_tools"]:
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {"tools": MCP_TOOL_DEFINITIONS}
        }
    elif req.method in ["tools/call", "call_tool"]:
        params = req.params or {}
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            res = dispatch_tool_call(name, args)
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(res, default=str)}],
                    "isError": False
                }
            }
        except Exception as err:
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "error": {"code": -32603, "message": str(err)},
                "result": {
                    "content": [{"type": "text", "text": f"Error: {err}"}],
                    "isError": True
                }
            }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "error": {"code": -32601, "message": f"Method '{req.method}' not found"}
        }

def run_stdio_mcp_server():
    """Run an interactive stdio MCP server loop for CLI / Claude / Cursor integrations."""
    print("[MCP Server] Starting Loop MCP stdio server...", file=sys.stderr)
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line.strip())
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOL_DEFINITIONS}}
            elif method == "tools/call":
                name = params.get("name")
                args = params.get("arguments", {})
                tool_res = dispatch_tool_call(name, args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(tool_res, default=str)}],
                        "isError": False
                    }
                }
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method '{method}' not found"}}
            
            print(json.dumps(resp), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    run_stdio_mcp_server()
