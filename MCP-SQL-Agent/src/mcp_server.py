import logging
import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


# ============================================================
# Configuration
# ============================================================

load_dotenv()

# server.py:
# project/src/mcp_text2sql/server.py
#
# parents[0] -> mcp_text2sql
# parents[1] -> src
# parents[2] -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

env_db_path = os.getenv("DATABASE_PATH", "")

if env_db_path:
    db_path = Path(env_db_path)

    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path

    DB_PATH = db_path.resolve()

else:
    DB_PATH = (PROJECT_ROOT / "data" / "sample.db").resolve()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

logger = logging.getLogger("text2sql-mcp")


# ============================================================
# MCP Server
# ============================================================

mcp = FastMCP("Text2SQL MCP Server")


# ============================================================
# Helpers
# ============================================================

def _get_connection() -> sqlite3.Connection:
    """
    Return a connection to the SQLite database.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Run 'uv run python scripts/setup_db.py' first."
        )

    conn = sqlite3.connect(str(DB_PATH))

    # Allows rows to behave like dictionaries
    conn.row_factory = sqlite3.Row

    return conn


def _get_tables_list() -> list[str]:
    """
    Return the list of user-created tables.
    """

    conn = _get_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
            """
        )

        return [row[0] for row in cur.fetchall()]

    finally:
        conn.close()


def _validate_table_name(table_name: str) -> None:
    """
    Validate that the requested table actually exists.
    """

    tables = _get_tables_list()

    if table_name not in tables:
        raise ValueError(
            f"Table '{table_name}' does not exist. "
            f"Available tables: {', '.join(tables)}"
        )


def _get_schema(table_name: str) -> dict:
    """
    Return schema information for a table.
    """

    _validate_table_name(table_name)

    conn = _get_connection()

    try:
        cur = conn.cursor()

        cur.execute(f'PRAGMA table_info("{table_name}")')

        columns = []

        for row in cur.fetchall():
            columns.append(
                {
                    "name": row["name"],
                    "type": row["type"],
                    "not_null": bool(row["notnull"]),
                    "default": row["dflt_value"],
                    "primary_key": bool(row["pk"]),
                }
            )

        cur.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        )

        create_row = cur.fetchone()

        return {
            "table": table_name,
            "columns": columns,
            "create_sql": create_row["sql"] if create_row else None,
        }

    finally:
        conn.close()


def _is_read_only_sql(sql: str) -> bool:
    """
    Only allow read-only SQL through the MCP tool.
    """

    cleaned = sql.strip()

    # Remove SQL comments
    cleaned = re.sub(r"--.*?$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip().lower()

    return cleaned.startswith("select") or cleaned.startswith("with")


# ============================================================
# MCP TOOL 1: List Tables
# ============================================================

@mcp.tool()
def list_tables() -> list[str]:
    """
    List all tables available in the SQLite database.

    Use this tool before generating SQL when you need to know
    which tables are available.
    """

    logger.info("Listing database tables")

    return _get_tables_list()


# ============================================================
# MCP TOOL 2: Get Table Schema
# ============================================================

@mcp.tool()
def get_table_schema(table_name: str) -> dict:
    """
    Get schema information for a specific database table.

    Returns column names, data types, primary key information,
    nullability and the CREATE TABLE statement.

    Args:
        table_name: Name of the table whose schema should be returned.
    """

    logger.info("Getting schema for table: %s", table_name)

    return _get_schema(table_name)


# ============================================================
# MCP TOOL 3: Execute SQL
# ============================================================

@mcp.tool()
def execute_sql(sql: str) -> dict:
    """
    Execute a read-only SQL query against the SQLite database.

    Only SELECT queries and read-only WITH queries are allowed.

    Args:
        sql: SQL query to execute.
    """

    logger.info("Executing SQL: %s", sql)

    if not _is_read_only_sql(sql):
        raise ValueError(
            "Only read-only SELECT/WITH queries are allowed."
        )

    conn = _get_connection()

    try:
        cur = conn.cursor()

        cur.execute(sql)

        rows = cur.fetchall()

        columns = (
            [description[0] for description in cur.description]
            if cur.description
            else []
        )

        results = [
            dict(zip(columns, row))
            for row in rows
        ]

        return {
            "columns": columns,
            "rows": results,
            "row_count": len(results),
        }

    except sqlite3.Error as exc:
        logger.exception("SQL execution failed")
        raise ValueError(f"SQL execution failed: {exc}") from exc

    finally:
        conn.close()


# ============================================================
# MCP RESOURCE: Database Schema
# ============================================================

@mcp.resource("schema://database")
def database_schema() -> str:
    """
    Return the complete schema of the database.

    This resource gives an MCP client/host context about the
    database structure without executing a query.
    """

    tables = _get_tables_list()

    schema_parts = []

    for table in tables:
        schema = _get_schema(table)

        schema_parts.append(
            schema["create_sql"]
        )

    return "\n\n".join(schema_parts)


# ============================================================
# MCP PROMPT: Text-to-SQL Assistant
# ============================================================

@mcp.prompt()
def text_to_sql(question: str) -> str:
    """
    Prompt template for converting a natural-language question
    into SQL using the available MCP database tools.

    Args:
        question: Natural-language database question.
    """

    return f"""
You are a Text-to-SQL assistant connected to a SQLite database.

Your job is to answer the user's question using the database.

User question:

{question}

Instructions:

1. Inspect the available database tables using list_tables.
2. Inspect relevant table schemas using get_table_schema.
3. Generate valid SQLite SQL based only on the available schema.
4. Never invent tables or columns.
5. Use JOINs when information is spread across multiple tables.
6. Use execute_sql to execute the generated SQL.
7. Only generate read-only SQL.
8. Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
   REPLACE, TRUNCATE or other data-modifying statements.
9. After executing the query, explain the result clearly to the user.
"""


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    logger.info("Starting Text2SQL MCP Server")
    logger.info("Database: %s", DB_PATH)

    mcp.run()