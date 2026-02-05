---
title: Loomis Brain Service - Architecture Diagram
---

flowchart TD
    UI["User Chat UI (index.html)"]
    API["FastAPI /chat Endpoint (main.py)"]
    DB["SQLite Conversation DB (conversation_db.py)"]
    Graph["LangGraph Orchestration (graph.py)"]
    State["BrainState (state.py)"]
    DM["Dialogue Manager Agent"]
    Router["Router Agent"]
    Pricing["Pricing Agent"]
    Governance["Governance Agent"]
    Label["Label Agent"]
    Tracking["Tracking Agent"]
    MCP["MCP Client (mcp_client.py)\nJSON-RPC to Go Execution Server"]
    Prompts["Prompts (prompts/*.txt)"]
    LLM["Gemini LLM (llm_client.py)"]

    UI -->|POST message| API
    API -->|Store/retrieve| DB
    API -->|Create/Update| State
    API -->|Invoke| Graph
    Graph --> DM
    DM -->|Slot-filling, Extraction| State
    DM -->|Intent| Router
    Router -->|LLM| LLM
    Router -->|Intent| State
    Graph --> Pricing
    Pricing -->|Rates| State
    Pricing --> MCP
    Graph --> Governance
    Governance -->|Approval| State
    Graph --> Label
    Label -->|Label| State
    Label --> MCP
    Graph --> Tracking
    Tracking -->|Tracking| State
    Tracking --> MCP
    Graph -->|Final State| API
    API -->|Return| UI
    DM -->|Prompts| Prompts
    Pricing -->|Prompts| Prompts
    Tracking -->|Prompts| Prompts
    Governance -->|Prompts| Prompts
