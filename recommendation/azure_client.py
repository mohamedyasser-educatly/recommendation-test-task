from __future__ import annotations

import os

from langchain_openai import AzureChatOpenAI, ChatOpenAI

from recommendation.env import MissingEnvError, require_env


class AzureLLMConfigError(MissingEnvError):
    """Azure OpenAI / AI Foundry configuration error."""


def _uses_openai_v1_endpoint(endpoint: str) -> bool:
    normalized = endpoint.rstrip("/")
    return normalized.endswith("/openai/v1") or "/openai/v1/" in f"{normalized}/"


def build_azure_chat_llm(*, temperature: float = 0.4):
    """Create an Azure OpenAI / Azure AI Foundry chat client from environment variables."""
    try:
        endpoint = require_env("AZURE_OPENAI_ENDPOINT").rstrip("/")
        api_key = require_env("AZURE_OPENAI_API_KEY")
        deployment_name = require_env("AZURE_OPENAI_DEPLOYMENT_NAME")
    except MissingEnvError as exc:
        raise AzureLLMConfigError(str(exc)) from exc

    if _uses_openai_v1_endpoint(endpoint):
        return ChatOpenAI(
            base_url=endpoint,
            api_key=api_key,
            model=deployment_name,
            temperature=temperature,
        )

    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview").strip()
    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version=api_version,
        temperature=temperature,
    )
