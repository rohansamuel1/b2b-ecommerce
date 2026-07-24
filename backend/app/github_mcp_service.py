"""Read-only client for GitHub's official remote MCP server."""
from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

MCP_URL = "https://api.githubcopilot.com/mcp/"
ALLOWED_TOOLS = {
    "actions_list",
    "get_commit",
    "get_file_contents",
    "get_latest_release",
    "list_issues",
    "pull_request_read",
    "search_code",
}


def configured() -> bool:
    return bool(
        os.getenv("MCP_GITHUB_ENABLED", "false").lower() == "true"
        and os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        and os.getenv("GITHUB_REPOSITORY")
    )


def repository_parts() -> tuple[str, str]:
    value = os.getenv("GITHUB_REPOSITORY", "").strip().strip("/")
    if value.count("/") != 1:
        raise RuntimeError("GITHUB_REPOSITORY must use owner/repository format")
    return tuple(value.split("/", 1))


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("GITHUB_PERSONAL_ACCESS_TOKEN is not configured")
    return {
        "Authorization": f"Bearer {token}",
        "X-MCP-Readonly": "true",
        "X-MCP-Toolsets": os.getenv(
            "GITHUB_MCP_TOOLSETS", "repos,issues,pull_requests,actions"
        ),
    }


async def _session_operation(tool: str | None = None, arguments: dict | None = None):
    async with httpx.AsyncClient(headers=_headers(), timeout=30) as client:
        async with streamable_http_client(MCP_URL, http_client=client) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                initialized = await session.initialize()
                tools = await session.list_tools()
                if tool is None:
                    return {
                        "connected": True,
                        "server": initialized.serverInfo.name,
                        "version": initialized.serverInfo.version,
                        "tools": [item.name for item in tools.tools if item.name in ALLOWED_TOOLS],
                    }
                available = {item.name for item in tools.tools}
                if tool not in ALLOWED_TOOLS or tool not in available:
                    raise RuntimeError(f"GitHub MCP tool is not allowed or unavailable: {tool}")
                result = await session.call_tool(tool, arguments or {})
                return result.model_dump(mode="json")


def _run(coroutine):
    return asyncio.run(coroutine)


def status() -> dict[str, Any]:
    if not configured():
        return {"configured": False, "connected": False, "read_only": True}
    try:
        result = _run(_session_operation())
        owner, repo = repository_parts()
        return {"configured": True, "read_only": True, "repository": f"{owner}/{repo}", **result}
    except Exception as exc:
        return {"configured": True, "connected": False, "read_only": True, "error": str(exc)}


def call(tool: str, arguments: dict | None = None) -> dict[str, Any]:
    if not configured():
        raise RuntimeError("GitHub MCP is not configured")
    owner, repo = repository_parts()
    payload = dict(arguments or {})
    if tool != "search_code":
        payload["owner"] = owner
        payload["repo"] = repo
    elif f"repo:{owner}/{repo}" not in str(payload.get("query", "")):
        payload["query"] = f"{payload.get('query', '').strip()} repo:{owner}/{repo}".strip()
    return _run(_session_operation(tool, payload))
