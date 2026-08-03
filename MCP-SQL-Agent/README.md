# MCP SQL Agent

An end-to-end **Agentic Text-to-SQL system** built using the
**Model Context Protocol (MCP)**, a **ReAct-style AI agent**,
**GPT-OSS-20B via Groq**, and **SQLite**.

The application allows users to ask natural-language questions about
a relational database. The AI agent dynamically discovers the database
schema, selects MCP tools, generates SQL, executes queries, observes
the results, and returns a natural-language answer.

---

## Overview

This project demonstrates how an LLM can interact with an external
database through the **Model Context Protocol (MCP)** rather than
accessing the database directly.

The system contains three main components:

- **MCP Server** — exposes database capabilities as MCP tools,
  resources, and prompts.
- **MCP Client** — communicates with the MCP server using
  stdin/stdout (stdio).
- **ReAct Agent** — uses an LLM to reason about user questions,
  select MCP tools, observe results, and generate final answers.

---

## Architecture

```text
                    ┌─────────────────────┐
                    │        User         │
                    │ Natural Language    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    ReAct Agent      │
                    │     agent.py        │
                    └──────────┬──────────┘
                               │
                     Reason / Tool Calling
                               │
                               ▼
                    ┌─────────────────────┐
                    │   GPT-OSS-20B       │
                    │     via Groq        │
                    └──────────┬──────────┘
                               │
                         Tool Decision
                               │
                               ▼
                    ┌─────────────────────┐
                    │    MCP Client       │
                    │   mcp_client.py     │
                    └──────────┬──────────┘
                               │
                           MCP / stdio
                               │
                               ▼
                    ┌─────────────────────┐
                    │    MCP Server       │
                    │   mcp_server.py     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
         list_tables    get_table_schema    execute_sql
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       SQLite        │
                    │   data/sample.db    │
                    └─────────────────────┘