"""
MCP Client for the Text-to-SQL project.

The client communicates with the MCP server using stdio.

Responsibilities:
- Start/connect to the MCP server
- List available tools
- Call tools
- List resources
- Read resources
- List prompts
- Get prompts
"""

import asyncio
import json
import logging
import sys
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


logger = logging.getLogger("text2sql-client")


class Text2SQLMCPClient:

    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

    # ========================================================
    # Connection
    # ========================================================

    async def connect(self):
        """
        Start the MCP server as a subprocess and establish
        an MCP session over stdin/stdout.
        """

        server_params = StdioServerParameters(
            command="uv",
            args=[
                "run",
                "python",
                "src/mcp_server.py",
            ],
            env=None,
        )

        logger.info("Starting MCP server...")

        read_stream, write_stream = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(
                read_stream,
                write_stream,
            )
        )

        await self.session.initialize()

        logger.info("Connected to MCP server.")

    # ========================================================
    # Tools
    # ========================================================

    async def list_tools(self):
        """
        Return all tools exposed by the MCP server.
        """

        if self.session is None:
            raise RuntimeError("Client is not connected.")

        response = await self.session.list_tools()

        return response.tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ):
        """
        Call a tool exposed by the MCP server.
        """

        if self.session is None:
            raise RuntimeError("Client is not connected.")

        if arguments is None:
            arguments = {}

        logger.info(
            "Calling tool '%s' with arguments: %s",
            name,
            arguments,
        )

        result = await self.session.call_tool(
            name,
            arguments=arguments,
        )

        return result

    # ========================================================
    # Resources
    # ========================================================

    async def list_resources(self):
        """
        Return all resources exposed by the MCP server.
        """

        if self.session is None:
            raise RuntimeError("Client is not connected.")

        response = await self.session.list_resources()

        return response.resources

    async def read_resource(self, uri: str):
        """
        Read a resource exposed by the MCP server.
        """

        if self.session is None:
            raise RuntimeError("Client is not connected.")

        result = await self.session.read_resource(uri)

        return result

    # ========================================================
    # Prompts
    # ========================================================

    async def list_prompts(self):
        """
        Return all prompts exposed by the MCP server.
        """

        if self.session is None:
            raise RuntimeError("Client is not connected.")

        response = await self.session.list_prompts()

        return response.prompts

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None,
    ):
        """
        Retrieve a prompt from the MCP server.
        """

        if self.session is None:
            raise RuntimeError("Client is not connected.")

        if arguments is None:
            arguments = {}

        result = await self.session.get_prompt(
            name,
            arguments=arguments,
        )

        return result

    # ========================================================
    # Cleanup
    # ========================================================

    async def close(self):
        """
        Close the MCP session and server process.
        """

        await self.exit_stack.aclose()

        self.session = None

        logger.info("MCP client closed.")


# ============================================================
# Demo / Test
# ============================================================

async def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    client = Text2SQLMCPClient()

    try:

        # ----------------------------------------------------
        # Connect
        # ----------------------------------------------------

        await client.connect()

        print("\n========================================")
        print("AVAILABLE TOOLS")
        print("========================================")

        tools = await client.list_tools()

        for tool in tools:
            print(f"\nTool: {tool.name}")
            print(f"Description: {tool.description}")

            if tool.inputSchema:
                print(
                    "Input Schema:",
                    json.dumps(
                        tool.inputSchema,
                        indent=2,
                    ),
                )

        # ----------------------------------------------------
        # Call list_tables
        # ----------------------------------------------------

        print("\n========================================")
        print("CALL TOOL: list_tables")
        print("========================================")

        result = await client.call_tool(
            "list_tables"
        )

        print(result)

        # ----------------------------------------------------
        # Call get_table_schema
        # ----------------------------------------------------

        print("\n========================================")
        print("CALL TOOL: get_table_schema")
        print("========================================")

        result = await client.call_tool(
            "get_table_schema",
            {
                "table_name": "customers"
            },
        )

        print(result)

        # ----------------------------------------------------
        # Execute SQL
        # ----------------------------------------------------

        print("\n========================================")
        print("CALL TOOL: execute_sql")
        print("========================================")

        result = await client.call_tool(
            "execute_sql",
            {
                "sql": """
                    SELECT
                        company_name,
                        country,
                        credit_limit
                    FROM customers
                    WHERE country = 'Germany'
                    ORDER BY credit_limit DESC
                """
            },
        )

        print(result)

        # ----------------------------------------------------
        # Resources
        # ----------------------------------------------------

        print("\n========================================")
        print("AVAILABLE RESOURCES")
        print("========================================")

        resources = await client.list_resources()

        for resource in resources:
            print(f"\nResource: {resource.name}")
            print(f"URI: {resource.uri}")
            print(f"Description: {resource.description}")

        # ----------------------------------------------------
        # Read our schema resource
        # ----------------------------------------------------

        print("\n========================================")
        print("DATABASE SCHEMA RESOURCE")
        print("========================================")

        schema = await client.read_resource(
            "schema://database"
        )

        print(schema)

        # ----------------------------------------------------
        # Prompts
        # ----------------------------------------------------

        print("\n========================================")
        print("AVAILABLE PROMPTS")
        print("========================================")

        prompts = await client.list_prompts()

        for prompt in prompts:
            print(f"\nPrompt: {prompt.name}")
            print(f"Description: {prompt.description}")

        # ----------------------------------------------------
        # Get Text-to-SQL prompt
        # ----------------------------------------------------

        print("\n========================================")
        print("TEXT-TO-SQL PROMPT")
        print("========================================")

        prompt = await client.get_prompt(
            "text_to_sql",
            {
                "question":
                    "Which German customer has spent the most money?"
            },
        )

        print(prompt)

    finally:

        await client.close()


if __name__ == "__main__":
    asyncio.run(main())