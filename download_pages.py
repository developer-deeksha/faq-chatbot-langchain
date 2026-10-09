# download_pages.py
# Uses MCP to download all pages from your Confluence space
# and saves them in data/confluence_pages.json

import asyncio
import json
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

# How to START the MCP server (same as before)
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
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to MCP server!")

            # PART 1: search to get the LIST of pages in our space
            query = f'type=page AND space="{space_key}"'
            result = await session.call_tool(
                "confluence_search",
                {"query": query, "limit": 50},
            )
            pages = json.loads(result.content[0].text)
            if isinstance(pages, dict):
                pages = pages.get("results", [])
            print("Pages found:", len(pages))

            # PART 2: for each page, get its FULL text
            saved_pages = []
            for item in pages:
                if "id" not in item:
                    print("This item has no id. Its keys are:", list(item.keys()))
                    continue

                page_id = str(item["id"])
                title = item.get("title", "Untitled")

                page_result = await session.call_tool(
                    "confluence_get_page",
                    {"page_id": page_id},
                )
                page_text = page_result.content[0].text

                # the text normally comes as JSON; take the content out of it
                try:
                    page_data = json.loads(page_text)
                    page_data = page_data.get("metadata", page_data)
                    content = page_data["content"]["value"]
                except Exception:
                    content = page_text   # if it is not JSON, use it as it is

                print(f"- {title}: {len(content)} characters")

                if len(content) < 20:
                    print("  (too short, skipped)")
                    continue

                saved_pages.append({
                    "id": page_id,
                    "title": title,
                    "url": item.get("url", ""),
                    "content": content,
                })

    # PART 3: save everything in a JSON file
    os.makedirs("data", exist_ok=True)
    with open("data/confluence_pages.json", "w", encoding="utf-8") as f:
        json.dump(saved_pages, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(saved_pages)} pages to data/confluence_pages.json")


asyncio.run(main())