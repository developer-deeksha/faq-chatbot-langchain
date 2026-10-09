# my_mcp_client.py
# Connects to the Confluence MCP server and searches your space.

import asyncio
import os

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Read the values from the .env file
load_dotenv()
confluence_url = os.getenv("CONFLUENCE_URL")
email = os.getenv("CONFLUENCE_USERNAME")
token = os.getenv("CONFLUENCE_API_TOKEN")
space_key = os.getenv("CONFLUENCE_SPACE_KEY")

if not (confluence_url and email and token and space_key):
    print("Something is missing in your .env file")
    raise SystemExit

# PART A: how to START the MCP server
server_params = StdioServerParameters(
    command="uvx",
    args=["mcp-atlassian"],
    env={
        "CONFLUENCE_URL": confluence_url,
        "CONFLUENCE_USERNAME": email,
        "CONFLUENCE_API_TOKEN": token,
        "ENABLED_TOOLS": "confluence_search,confluence_get_page",
    },
)


async def main():
    # PART B: start the server and connect to it
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # PART C: say hello to the server
            await session.initialize()
            print("Connected to MCP server!")

            # PART D: ask the server what tools it has
            tools = await session.list_tools()
            print("Tools available:")
            for tool in tools.tools:
                print("  -", tool.name)

            # PART E: use a tool - search pages in our space
            query = f'type=page AND space="{space_key}"'
            result = await session.call_tool(
                "confluence_search",
                {"query": query, "limit": 3},
            )

            # PART F: print the answer
            print("\nSearch result:")
            print(result.content[0].text)


asyncio.run(main())