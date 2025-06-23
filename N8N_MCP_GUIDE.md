# n8n MCP Integration Guide

This guide explains how to integrate the Shift Scheduler MCP server with n8n workflows.

## Prerequisites

1. **n8n with LangChain nodes**: Ensure you have n8n installed with the LangChain community nodes
2. **Running servers**:
   - Shift Scheduler API: `make run` (port 8081)
   - MCP Server in SSE mode: `make mcp-sse` (port 8082)

## Setup Instructions

### 1. Start the Servers

```bash
# Terminal 1: Start the API server
make run

# Terminal 2: Start the MCP server in SSE mode
make mcp-sse
```

The MCP server will be available at `http://localhost:8082/sse`

### 2. Import the Example Workflow

1. Open n8n
2. Create a new workflow
3. Import the example workflow from `examples/n8n-mcp-workflow.json`

### 3. Configure the MCP Client Node

The MCP Client node should be configured with:
- **SSE Endpoint**: `http://localhost:8082/sse`

### 4. Connect the Nodes

The MCP Client must be connected to an Agent node:
1. **MCP Client** → **Agent** (ai_tool connection)
2. **LLM (e.g., OpenAI)** → **Agent** (ai_languageModel connection)
3. **Input** → **Agent** → **Output**

## Available MCP Tools

### Basic Operations
- `health_check` - Check API health status
- `get_demo_schedule` - Get demo shift schedule
- `solve_schedule_sync` - Synchronous schedule optimization
- `solve_schedule_async` - Asynchronous optimization
- `get_solve_status` - Check job status

### Analysis Tools
- `analyze_weekly_hours` - Analyze weekly work hours
- `test_weekly_constraints` - Test constraints with demo data
- `get_schedule_shifts` - Get detailed shift information

### Employee Management
- `add_employee_to_job` - Add employee to schedule
- `update_employee_skills` - Update employee skills
- `reassign_shift` - Reassign shifts

### Report Generation
- `get_schedule_html_report` - Generate HTML reports

## Example Prompts

Here are some example prompts you can use with the agent:

1. **Basic Health Check**:
   ```
   Check if the shift scheduler API is working
   ```

2. **Get Demo Schedule**:
   ```
   Get a demo shift schedule and show me the results
   ```

3. **Analyze Schedule**:
   ```
   Get the demo schedule and analyze the weekly hours. 
   Tell me about any constraint violations.
   ```

4. **Optimize Schedule**:
   ```
   Create a shift schedule for 5 employees with different skills 
   and optimize it for fairness.
   ```

## Troubleshooting

### MCP Client Connection Error
- Ensure the MCP server is running: `make mcp-sse`
- Verify the endpoint URL: `http://localhost:8082/sse`
- Check if port 8082 is available

### No Tools Available
- The MCP server should automatically expose all tools
- Check the MCP server logs for any errors
- Ensure the API server is also running

### Agent Not Finding Tools
- Make sure the MCP Client is connected to the Agent's ai_tool input
- The connection must be properly established before running

## Advanced Configuration

### Custom Port
```bash
MCP_SERVER_PORT=8083 make mcp-sse
```
Then update the SSE endpoint in n8n to `http://localhost:8083/sse`

### Different Host
```bash
MCP_SERVER_HOST=0.0.0.0 make mcp-sse
```

### Using HTTP Mode Instead
```bash
make mcp-http
```
Then use `http://localhost:8082` as the endpoint (without `/sse`)

## Security Notes

- The example uses no authentication for simplicity
- In production, consider adding authentication to the MCP server
- Use environment variables for sensitive configuration