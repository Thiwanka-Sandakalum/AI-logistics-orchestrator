---
title: Loomis Brain Service - Data Flow Diagram
---

flowchart TD
    User["User"]
    UI["Chat UI (index.html)"]
    API["FastAPI Backend (main.py)"]
    DB["SQLite DB (conversation_db.py)"]
    LangGraph["LangGraph StateGraph (graph.py)"]
    State["BrainState (state.py)"]
    Agents["Agents (dialogue_manager, router, pricing, label, tracking, governance)"]
    MCP["MCP Client (mcp_client.py)"]
    GoExec["Go Execution Server"]
    LLM["Gemini LLM (llm_client.py)"]
    Prompts["Prompts (prompts/*.txt)"]

    User -->|Message| UI
    UI -->|POST /chat| API
    API -->|Store/Fetch| DB
    API -->|Create/Update| State
    API -->|Invoke| LangGraph
    LangGraph -->|State| Agents
    Agents -->|Tool Calls| MCP
    MCP -->|JSON-RPC| GoExec
    Agents -->|LLM| LLM
    Agents -->|Prompts| Prompts
    Agents -->|Update| State
    LangGraph -->|Final State| API
    API -->|Return Response| UI
    UI -->|Show| User
