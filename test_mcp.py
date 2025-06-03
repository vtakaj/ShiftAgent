#!/usr/bin/env python3
"""Test MCP server connection to API"""

import asyncio
import httpx
import os

API_URL = os.getenv("SHIFT_SCHEDULER_API_URL", "http://localhost:8081")

async def test_connection():
    print(f"Testing connection to API at: {API_URL}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get(f"{API_URL}/health")
            print(f"Health check status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Test demo endpoint
            response = await client.get(f"{API_URL}/api/shifts/demo")
            print(f"\nDemo endpoint status: {response.status_code}")
            print(f"Demo data keys: {list(response.json().keys())}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())