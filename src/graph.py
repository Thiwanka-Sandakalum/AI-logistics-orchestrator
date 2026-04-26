"""Courier Service Assistant Agent Graph Definition."""

from dotenv import load_dotenv
load_dotenv()

from langchain.agents import create_agent
from src.agent.middleware import build_middleware
from src.agent.model import build_model, get_normalized_model_name
from src.agent.prompt import SYSTEM_PROMPT
from src.agent.tools import TOOLS

model_name = get_normalized_model_name()
model = build_model()
middleware = build_middleware(model_name)

# Create the compiled LangGraph agent using LangChain's create_agent API
graph = create_agent(
    model=model,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    middleware=middleware,
)
