from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from recommendation.azure_client import AzureLLMConfigError, build_azure_chat_llm
from recommendation.llm.errors import RecommendationLLMError
from recommendation.llm.usage import build_usage_record


@dataclass
class StructuredInvokeResult:
    parsed: BaseModel
    usage: dict[str, Any]


def build_structured_llm(output_model: type[BaseModel], *, temperature: float = 0.4):
    try:
        llm = build_azure_chat_llm(temperature=temperature)
    except AzureLLMConfigError as exc:
        raise RecommendationLLMError(str(exc)) from exc
    return llm.with_structured_output(output_model, include_raw=True)


def invoke_structured(
    output_model: type[BaseModel],
    *,
    system_prompt: str,
    user_prompt: str,
    step: str,
    temperature: float = 0.4,
    error_prefix: str = "LLM request failed",
) -> StructuredInvokeResult:
    structured_llm = build_structured_llm(output_model, temperature=temperature)
    try:
        result = structured_llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
    except Exception as exc:  # noqa: BLE001
        raise RecommendationLLMError(f"{error_prefix}: {exc}") from exc

    if isinstance(result, dict) and "parsed" in result:
        parsed = result["parsed"]
        raw_message = result.get("raw")
    else:
        parsed = result
        raw_message = None

    if not isinstance(parsed, output_model):
        raise RecommendationLLMError(f"{error_prefix}: unexpected response type.")

    usage = build_usage_record(raw_message, step=step)
    return StructuredInvokeResult(parsed=parsed, usage=usage)
