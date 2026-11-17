import sys, json
from client import AgentContextDynamicCompressor

def handle_mcp():
    comp = AgentContextDynamicCompressor()
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print(json.dumps(comp.run_benchmark_compression(), indent=2))
        return

    for line in sys.stdin:
        if not line.strip(): continue
        try:
            try:
                req = json.loads(line)
            except json.JSONDecodeError as exc:
                print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}), flush=True)
                continue
            if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or not isinstance(req.get("method"), str):
                print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}), flush=True)
                continue
            # JSON-RPC notifications never receive a response or execute request-only tools.
            if "id" not in req:
                continue
            if req["method"] == "initialize":
                print(json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": {
                    "protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                    "serverInfo": {"name": 'genpark-agent-context-dynamic-compressor-skill', "version": "1.0.0"}
                }}), flush=True)
                continue
            if req["method"] == "ping":
                print(json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": {}}), flush=True)
                continue
            if req["method"] not in ("tools/list", "tools/call"):
                print(json.dumps({"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32601, "message": "Method not found"}}), flush=True)
                continue
            if req["method"] == "tools/call":
                params = req.get("params")
                if not isinstance(params, dict) or not isinstance(params.get("arguments", {}), dict) or params.get("name") not in ('compress_text_context', 'compact_json_tool_outputs', 'run_benchmark_compression'):
                    print(json.dumps({"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32602, "message": "Unknown tool or invalid arguments"}}), flush=True)
                    continue
            method = req.get("method")
            msg_id = req.get("id")
            
            if method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": [
                    {"name": "compress_text_context", "description": "Prune repetitive boilerplate while preserving core facts.", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}},
                    {"name": "compact_json_tool_outputs", "description": "Strip nulls and empty metadata from agent tool returns.", "inputSchema": {"type": "object", "properties": {"payload": {"type": "object"}}}},
                    {"name": "run_benchmark_compression", "description": "Run comprehensive context compression benchmark.", "inputSchema": {"type": "object"}}
                ]}}
            elif method == "tools/call":
                tname = req.get("params", {}).get("name")
                args = req.get("params", {}).get("arguments", {})
                if tname == "compress_text_context":
                    res = comp.compress_text_context(args.get("text", ""))
                elif tname == "compact_json_tool_outputs":
                    res = comp.compact_json_tool_outputs(args.get("payload", {}))
                else:
                    res = comp.run_benchmark_compression()
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}}
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}}
            
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req.get("id") if isinstance(req, dict) else None, "error": {"code": -32000, "message": str(e)}}) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    handle_mcp()
