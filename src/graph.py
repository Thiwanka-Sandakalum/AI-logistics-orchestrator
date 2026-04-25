"""Courier Service Assistant Agent Graph Definition."""

from dotenv import load_dotenv
load_dotenv()

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from src.config import settings
from src.tools.shipment_tools import track_shipment, create_shipment
from src.tools.customer_tools import lookup_customer
from src.tools.complaint_tools import file_complaint
from src.tools.rate_tools import get_shipping_quote
from src.tools.distance_and_rate_tool import calculate_distance_and_rates

# Compile the list of all available tools
tools = [
    track_shipment,
    create_shipment,
    lookup_customer,
    file_complaint,
    get_shipping_quote,
    calculate_distance_and_rates,
]

model_name = settings.model_id
if model_name.startswith("google:"):
    model_name = "google_genai:" + model_name[7:]
elif ":" not in model_name:
    model_name = f"google_genai:{model_name}"

# Initialize the Chat Model using configuration settings
model = init_chat_model(
    model=model_name,
    temperature=settings.model_temperature,
    max_tokens=settings.model_max_tokens,
)

# Define the persona and instructions for the agent
system_prompt = """You are Loomis, a helpful, professional, and efficient courier service assistant.
Your goal is to help customers manage their logistics and shipping needs.

You have access to a set of tools to perform tasks on behalf of the user. You can:
1. Track existing shipments using their 9-digit tracking numbers.
2. Provide shipping quotes and realistic rate calculations based on distance, weight, and dimensions.
3. Look up customer profiles and their recent shipping history using email or phone numbers.
4. Create new shipments and generate tracking numbers.
5. File formal complaints for damaged, missing, or delayed packages.

Always be polite and professional. If you encounter an error using a tool, explain the issue to the user clearly and ask for corrected information if necessary. When quoting prices, always present the fastest and cheapest options clearly.
"""

# Create the compiled LangGraph agent using LangChain's create_agent API
graph = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
)
