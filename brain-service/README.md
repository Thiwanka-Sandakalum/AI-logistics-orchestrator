# Brain Service Modular Project Structure

This project has been reorganized to follow a modular, maintainable structure suitable for scalable development.

## Folder Structure

```
src/
  api/         # API controllers and endpoints
  services/    # Business logic and service modules
  agents/      # Agent modules (dialogue, governance, etc.)
  models/      # Data models and schemas
  db/          # Database access and storage
  llm/         # LLM and MCP clients
  prompts/     # Prompt templates
  static/      # Static files (HTML, assets)
  state/       # State management

docs/          # Documentation
requirements.txt
pyproject.toml
README.md
```

## How to Use

- All main code is under the `src/` directory, grouped by responsibility.
- To run or develop, navigate to the relevant module inside `src/`.
- Configuration and documentation remain at the project root.

## Reorganizing Script

A shell script `reorg_project.sh` is provided to automate the reorganization. Run it with:

```bash
bash reorg_project.sh
```

## Contribution

- Add new modules in the appropriate subfolder under `src/`.
- Keep business logic, API, and data models separated for clarity and maintainability.

## License

[Specify your license here]
