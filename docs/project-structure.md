# Project Structure

This repository is organized to keep graph orchestration, domain tools, and operations assets clearly separated.

## Current Layout

```
.
├── langgraph.json                # LangGraph app entrypoints and env wiring
├── src/                          # Main Python package
│   ├── graph.py                  # Exported graph entrypoint (used by langgraph.json)
│   ├── config/
│   │   └── settings.py           # Runtime settings
│   ├── storage/
│   │   └── sqlite_db.py          # Data access + migrations
│   ├── agent/                    # Agent assembly modules
│   │   ├── model.py
│   │   ├── prompt.py
│   │   ├── tools.py
│   │   ├── middleware.py
│   │   └── checkpointer.py
│   └── tools/                    # Domain tool implementations
├── data/                         # Local sqlite data/checkpoints
├── docs/                         # Architecture and operational docs
├── tests/                        # Test suite (unit/integration)
└── .env.example                  # Environment template
```

## Directory Rules

- Keep graph construction logic in `src/agent/` and keep `src/graph.py` as a thin entrypoint.
- Keep all tool implementations in `src/tools/`.
- Put design and runbook documents in `docs/`.
- Add all new automated tests under `tests/`.
- Avoid putting temporary planning files in repository root.
