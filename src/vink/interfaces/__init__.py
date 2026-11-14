"""Interfaces: entry points that expose vink to people and programs.

Each interface (CLI, MCP server, and later an HTTP API or browser-extension
bridge) builds a container via :mod:`vink.bootstrap`, calls services, and maps
domain errors to its own conventions (exit codes, tool errors, HTTP statuses).
"""
