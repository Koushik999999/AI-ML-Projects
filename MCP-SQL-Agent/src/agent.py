"""
ReAct Agent / Host for the MCP Text-to-SQL project.

User
  ↓
ReAct Agent (GPT-OSS-20B via Groq)
  ↓
MCP Client
  ↓ stdio
MCP Server
  ↓
SQLite
"""

import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from mcp_client import Text2SQLMCPClient


# ============================================================
# Configuration
# ============================================================

load_dotenv()

MODEL = "openai/gpt-oss-20b"

MAX_REACT_ITERATIONS = 10


# ============================================================
# Logging
# ============================================================

logger = logging.getLogger("text2sql-agent")


# ============================================================
# Groq Client
# ============================================================

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY is not set. "
        "Add it to your .env file."
    )


llm_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """
You are a Text-to-SQL ReAct agent.

You have access to an MCP server connected to a SQLite database.

Your responsibility is to answer user questions about the database
accurately by reasoning about the request and using the available
MCP tools.

You follow a ReAct-style workflow:

Reason -> Act -> Observe -> Reason -> ... -> Final Answer


DATABASE WORKFLOW

When the user asks a question about the database:

1. Understand the user's request.

2. Discover available tables when necessary.

3. Inspect the schemas of relevant tables before writing SQL.

4. Determine relationships between tables using their schemas.

5. Construct valid SQLite SQL.

6. Execute the SQL using the MCP SQL execution tool.

7. Inspect the returned result.

8. If execution fails:
   - analyze the error,
   - inspect the schema again if necessary,
   - correct the SQL,
   - retry.

9. Give the user a clear answer based strictly on the returned data.


AVAILABLE CAPABILITIES

The MCP server provides tools for operations such as:

- listing database tables
- inspecting table schemas
- executing read-only SQL

Use the provided tools instead of assuming database structure.

The MCP server may also expose:

- database resources
- reusable prompts


IMPORTANT DATABASE RULES

Never invent:

- table names
- column names
- relationships
- database values
- query results

The MCP database is the source of truth.

If you do not know the database structure, inspect it.


SQL SAFETY

Only use read-only SQL.

Allowed:

SELECT
WITH ... SELECT

Never attempt:

INSERT
UPDATE
DELETE
DROP
ALTER
CREATE
REPLACE
TRUNCATE

Never modify the database.


SQL QUALITY

Use appropriate SQLite features including:

- WHERE for filtering
- JOIN for relationships
- GROUP BY for aggregation
- HAVING for aggregate filtering
- ORDER BY for sorting and ranking
- LIMIT where appropriate
- COUNT
- SUM
- AVG
- MIN
- MAX


TOOL USAGE

Use tools only when needed.

Do not repeatedly call a tool when you already have the required
information.

If SQL execution produces an error, use the error as an observation
and correct your approach.


FINAL RESPONSE

Do not expose private chain-of-thought or hidden reasoning.

Return:

1. A clear answer to the user's question.
2. Relevant database values.
3. A concise explanation when useful.

You may show the SQL query when it would help the user understand
how the answer was obtained.
"""


# ============================================================
# ReAct Agent
# ============================================================

class Text2SQLAgent:

    def __init__(self):

        self.mcp_client = Text2SQLMCPClient()

        self.tools = []

    # ========================================================
    # Initialize
    # ========================================================

    async def initialize(self):
        """
        Connect to the MCP server and dynamically discover
        all available MCP tools.
        """

        await self.mcp_client.connect()

        mcp_tools = await self.mcp_client.list_tools()

        self.tools = self._convert_mcp_tools(
            mcp_tools
        )

        logger.info(
            "Agent initialized with %d MCP tools.",
            len(self.tools),
        )

    # ========================================================
    # Convert MCP tools to OpenAI/Groq tools
    # ========================================================

    def _convert_mcp_tools(self, mcp_tools):
        """
        Convert MCP tool definitions into the
        OpenAI-compatible function-calling format used by Groq.
        """

        groq_tools = []

        for tool in mcp_tools:

            groq_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": (
                            tool.description
                            or f"MCP tool: {tool.name}"
                        ),
                        "parameters": tool.inputSchema,
                    },
                }
            )

        return groq_tools

    # ========================================================
    # Execute MCP Tool
    # ========================================================

    async def _execute_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> str:
        """
        Execute a tool through the MCP client and convert
        its result into text that can be sent back to the LLM.
        """

        logger.info(
            "Executing MCP tool %s with %s",
            tool_name,
            arguments,
        )

        try:

            result = await self.mcp_client.call_tool(
                tool_name,
                arguments,
            )

            output = []

            for item in result.content:

                if hasattr(item, "text"):
                    output.append(item.text)

                else:
                    output.append(str(item))

            return "\n".join(output)

        except Exception as exc:

            logger.exception(
                "MCP tool '%s' failed.",
                tool_name,
            )

            return f"Tool execution error: {exc}"

    # ========================================================
    # ReAct Loop
    # ========================================================

    async def run(
        self,
        user_question: str,
    ) -> str:
        """
        Run the ReAct loop:

        Reason
          ↓
        Act
          ↓
        Observe
          ↓
        Reason
          ↓
        ...
          ↓
        Final Answer
        """

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_question,
            },
        ]

        for iteration in range(
            MAX_REACT_ITERATIONS
        ):

            logger.info(
                "ReAct iteration %d",
                iteration + 1,
            )

            # =================================================
            # REASON
            # =================================================

            response = (
                await llm_client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                )
            )

            assistant_message = (
                response.choices[0].message
            )

            # Add the model's response/tool decision
            # back into conversation history.

            messages.append(
                assistant_message.model_dump(
                    exclude_none=True
                )
            )

            # =================================================
            # No tool call = Final Answer
            # =================================================

            if not assistant_message.tool_calls:

                return (
                    assistant_message.content
                    or "Unable to produce an answer."
                )

            # =================================================
            # ACT
            # =================================================

            for tool_call in (
                assistant_message.tool_calls
            ):

                tool_name = (
                    tool_call.function.name
                )

                try:

                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                except json.JSONDecodeError:

                    arguments = {}

                print(
                    f"\n[ACT] {tool_name}"
                )

                print(
                    "[ARGS]",
                    json.dumps(
                        arguments,
                        indent=2,
                    ),
                )

                # Execute selected tool through MCP

                observation = (
                    await self._execute_tool(
                        tool_name,
                        arguments,
                    )
                )

                # =================================================
                # OBSERVE
                # =================================================

                print(
                    f"[OBSERVATION]\n"
                    f"{observation}\n"
                )

                # Send MCP observation back to the LLM

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": observation,
                    }
                )

            # Loop continues:
            #
            # Observation
            #     ↓
            # LLM reasons again
            #     ↓
            # Another tool call OR final answer

        return (
            "Maximum ReAct iterations reached "
            "without producing a final answer."
        )

    # ========================================================
    # MCP Resource Access
    # ========================================================

    async def get_database_schema(self):
        """
        Access the database schema MCP resource.
        """

        return await self.mcp_client.read_resource(
            "schema://database"
        )

    # ========================================================
    # MCP Prompt Access
    # ========================================================

    async def get_text2sql_prompt(
        self,
        question: str,
    ):
        """
        Retrieve the MCP Text-to-SQL prompt.
        """

        return await self.mcp_client.get_prompt(
            "text_to_sql",
            {
                "question": question
            },
        )

    # ========================================================
    # Cleanup
    # ========================================================

    async def close(self):

        await self.mcp_client.close()


# ============================================================
# Interactive Host
# ============================================================

async def main():

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "[%(levelname)s] "
            "%(name)s - %(message)s"
        ),
    )

    agent = Text2SQLAgent()

    try:

        print(
            "\nStarting Text-to-SQL "
            "ReAct Agent..."
        )

        await agent.initialize()

        print(
            f"LLM: {MODEL}"
        )

        print(
            "Provider: Groq"
        )

        print(
            "MCP server connected through stdio."
        )

        print(
            "\nAsk questions about the database."
        )

        print(
            "Type 'exit' or 'quit' to stop.\n"
        )

        # ====================================================
        # Conversation loop
        # ====================================================

        while True:

            question = input(
                "You: "
            ).strip()

            if not question:
                continue

            if question.lower() in {
                "exit",
                "quit",
            }:
                break

            try:

                answer = await agent.run(
                    question
                )

                print(
                    "\nAssistant:"
                )

                print(answer)

                print()

            except Exception as exc:

                logger.exception(
                    "Agent execution failed."
                )

                print(
                    f"\nError: {exc}\n"
                )

    finally:

        await agent.close()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())