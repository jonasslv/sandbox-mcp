# Python MCP Sandbox Tool

This tool provides a secure sandbox environment for executing Python scripts via the MCP (Model Communication Protocol). It runs scripts in isolated Docker containers with security constraints.

## Features

- **Secure Sandboxing**: Runs Python scripts in isolated Docker containers
- **Resource Limits**: 
  - Memory limit: 4096MB
  - CPU Cores: 4
  - Timeout: 120 seconds
- **Package Allowlist**: Only some curated packages are allowed
- **Read-Only Filesystem**: Container filesystem is read-only
- **Artifact Support**: Returns artifacts created during execution

## Usage

The tool expects a JSON request with a `script` field containing the Python code to execute.

Example request:
```json
{
  "script": "print('Hello from sandbox!')\nprint('This is a test script')"
}
```

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python mcp_sandbox_tool.py
```

## Response Format

The tool returns a JSON response with:
- `status`: "success" or "error"
- `stdout`: Standard output from the script
- `stderr`: Standard error from the script
- `return_code`: Exit code of the script
- `artifacts`: Files created during execution (if any)