"""Model initialization for the courier assistant agent."""

from langchain.chat_models import init_chat_model

from src.config import settings


def get_normalized_model_name() -> str:
    """Return model name in provider:model format expected by init_chat_model."""
    model_name = settings.model_id
    if model_name.startswith("google:"):
        return "google_genai:" + model_name[7:]
    if ":" not in model_name:
        return f"google_genai:{model_name}"
    return model_name


def build_model():
    """Build the configured chat model instance."""
    return init_chat_model(
        model=get_normalized_model_name(),
        temperature=settings.model_temperature,
        max_tokens=settings.model_max_tokens,
    )
