#!/usr/bin/env python3
"""
MCP Server entry point for Web-Scout.

This script runs Web-Scout as an MCP server for AI tools.
Usage: python mcp_server.py
"""

import sys
import os

# Add current directory to path so we can import main
sys.path.insert(0, os.path.dirname(__file__))

from main import main

if __name__ == "__main__":
    # Add --mcp flag to run as MCP server
    sys.argv.append("--mcp")
    main()