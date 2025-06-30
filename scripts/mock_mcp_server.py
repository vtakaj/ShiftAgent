#!/usr/bin/env python3
"""
Mock MCP server for manual testing of MCP protocol implementation
"""

import json
import sys


def main():
    print("Starting simple test MCP server", file=sys.stderr)

    while True:
        try:
            line = input()
            request = json.loads(line)

            if request.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {"listChanged": True}},
                        "serverInfo": {"name": "test-mcp-server", "version": "1.0.0"},
                    },
                }
            elif request.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "test_tool",
                                "description": "A simple test tool",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {
                                            "type": "string",
                                            "description": "Message to echo",
                                        }
                                    },
                                },
                            }
                        ]
                    },
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32601, "message": "Method not found"},
                }

            print(json.dumps(response))
            sys.stdout.flush()

        except EOFError:
            break
        except Exception as e:
            print(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": request.get("id") if "request" in locals() else None,
                        "error": {"code": -32603, "message": str(e)},
                    }
                )
            )
            sys.stdout.flush()


if __name__ == "__main__":
    main()
