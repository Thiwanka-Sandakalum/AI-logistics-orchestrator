# Loomis: Agentic Logistics & Shipping Orchestrator (MVP)

>  Autonomous AI-driven logistics orchestrator combining Python, Go, and Agentic Workflows. Designed for global shipping workflows with Human-in-the-Loop governance.

---

## Project Overview

**Loomis MVP** is a full-stack, agentic logistics orchestrator that demonstrates:

* **AI reasoning** with Python (LangGraph)
* **High-performance backend execution** with Go (MCP Server)
* **Enterprise-level patterns**: State Machine, Adapter, Circuit Breaker
* **Human-in-the-Loop (HITL)** for governance of high-value shipments
* **Cache & persistence** for reliability and cost savings

Unlike standard chatbots, Loomis **actively decides actions**—calculating shipping quotes, validating addresses, and simulating package tracking.

---

## Architecture

```mermaid
flowchart LR
    U[User] --> UI[Web UI / CLI]

    subgraph BRAIN["Cognitive Layer (Python / LangGraph)"]
        UI --> API[FastAPI / CLI Entry]
        API --> ROUTER[Router Agent]
        ROUTER --> STATE[State Machine]

        STATE -->|Quote Intent| PRICING[Pricing Agent]
        STATE -->|Validation| VALIDATOR[Validation Agent]
        STATE -->|Tracking| TRACKING[Tracking Agent]

        PRICING --> HITL{HITL Gate}
        HITL -->|Approved| COMPLETE[Workflow Complete]
        HITL -->|Rejected| CANCEL[Workflow Cancelled]
    end

    PRICING -->|MCP JSON-RPC| MCPCLIENT[MCP Client]
    VALIDATOR -->|MCP JSON-RPC| MCPCLIENT
    TRACKING -->|MCP JSON-RPC| MCPCLIENT

    subgraph EXEC["Execution Layer (Go / MCP Server)"]
        MCPCLIENT --> MCP[MCP Server]

        MCP --> TOOLREG[Tool Registry]

        TOOLREG --> QUOTE[get_shipping_quote]
        TOOLREG --> ADDR[validate_address]
        TOOLREG --> STATUS[get_tracking_status]

        QUOTE --> DHL[DHL Adapter (Mock)]
        ADDR --> MAPS[Maps / Geocoding (Mock)]
        STATUS --> TRACKSIM[Tracking Simulator]

        QUOTE --> CACHE[Redis Cache]
        QUOTE --> DB[(PostgreSQL)]
    end
```

**Key Principles:**

* **Brain (Python)**: AI reasoning, intent detection, workflow orchestration
* **Execution (Go)**: Secure tool execution, adapter pattern, API handling
* **Data Layer**: PostgreSQL (persistent storage) + Redis (caching)
* **HITL Gate**: Pauses workflow for high-value shipments (> $500)

---

## Technology Stack

| Layer            | Language / Tool | Purpose                                  |
| ---------------- | --------------- | ---------------------------------------- |
| Cognitive        | Python 3.10+    | Agent orchestration & reasoning          |
| AI Framework     | LangGraph       | Stateful agent workflows                 |
| Validation       | Pydantic        | Structured input/output                  |
| Backend          | Go (Golang)     | High-performance execution & tool server |
| Protocol         | MCP / JSON-RPC  | Python → Go communication                |
| Cache            | Redis           | Quote caching                            |
| Database         | PostgreSQL      | Persistent session & quote storage       |
| Containerization | Docker          | Environment reproducibility              |
| Cloud (optional) | Terraform       | Deploy infrastructure to AWS/GCP         |

---
## Core Components

| Component            | Description                                                              |
| -------------------- | ------------------------------------------------------------------------ |
| **Router Agent**     | Detects user intent and routes workflow                                  |
| **Pricing Agent**    | Prepares shipping quote requests                                         |
| **Validation Agent** | Cleans and validates user addresses                                      |
| **Tracking Agent**   | Fetches package status via Go backend                                    |
| **Governance Agent** | HITL logic for high-value shipments                                      |
| **MCP Server**       | Go backend exposing tools to Python                                      |
| **Tools / Adapters** | DHL Adapter (mock), Maps / Geocoding, Tracking Simulator                 |
| **State Machine**    | Enforces workflow: Idle → CollectingDetails → Quoting → HITL → Completed |
| **Cache & DB**       | Redis for quote caching, PostgreSQL for persistent storage               |

---

## Interaction Flow (Quote Example)

1. User submits shipment request (UI)
2. Brain Service detects **Quote intent** via Router Agent
3. State Machine moves to **CollectingDetails**
4. Validation Agent calls Go tool to **clean address**
5. Pricing Agent calls Go tool to **get_shipping_quote**
6. Go MCP Server validates input, queries DHL Adapter, caches quote
7. HITL Gate pauses if quote > $500
8. User confirms in UI
9. Brain completes workflow, updates DB & cache

---

## Business Value 

* Reduces manual customer support (AI automates quote & validation)
* Safe execution: AI **never touches API keys** directly
* HITL ensures high-value shipments are reviewed
* Caching & concurrency reduce latency and costs (~30% API cost savings)
* Demonstrates **AI reasoning + high-performance backend**, a rare hybrid skillset

---

## Future Enhancements

* Integrate real DHL, FedEx, and UPS APIs
* Full multi-language support
* Async event bus for real-time updates
* Extend frontend to full dashboard with tracking and history

---
