from __future__ import annotations

import os

from langchain_openai import AzureChatOpenAI

from recommendation.env import MissingEnvError, require_env


class AzureLLMConfigError(MissingEnvError):
    """Azure OpenAI / AI Foundry configuration error."""


def build_azure_chat_llm(*, temperature: float = 0.4) -> AzureChatOpenAI:
    """Create an Azure OpenAI / Azure AI Foundry chat client from environment variables."""
    try:
        endpoint = require_env("AZURE_OPENAI_ENDPOINT")
        api_key = require_env("AZURE_OPENAI_API_KEY")
        deployment_name = require_env("AZURE_OPENAI_DEPLOYMENT_NAME")
    except MissingEnvError as exc:
        raise AzureLLMConfigError(str(exc)) from exc

    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview").strip()

    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version=api_version,
        temperature=temperature,
    )
