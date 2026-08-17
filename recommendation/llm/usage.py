from __future__ import annotations

import os
from typing import Any


def get_llm_model_info() -> dict[str, str]:
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "unknown")
    return {
        "model": deployment,
        "deployment": deployment,
        "provider": "azure_openai",
    }


def extract_token_usage(raw_message: Any | None) -> dict[str, int]:
    if raw_message is None:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    usage_metadata = getattr(raw_message, "usage_metadata", None) or {}
    if usage_metadata:
        prompt_tokens = int(
            usage_metadata.get("input_tokens")
            or usage_metadata.get("prompt_tokens")
            or 0
        )
        completion_tokens = int(
            usage_metadata.get("output_tokens")
            or usage_metadata.get("completion_tokens")
            or 0
        )
        total_tokens = int(usage_metadata.get("total_tokens") or prompt_tokens + completion_tokens)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    response_metadata = getattr(raw_message, "response_metadata", None) or {}
    token_usage = response_metadata.get("token_usage") or {}
    prompt_tokens = int(token_usage.get("prompt_tokens") or 0)
    completion_tokens = int(token_usage.get("completion_tokens") or 0)
    total_tokens = int(token_usage.get("total_tokens") or prompt_tokens + completion_tokens)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def build_usage_record(raw_message: Any | None, *, step: str) -> dict[str, Any]:
    tokens = extract_token_usage(raw_message)
    model_info = get_llm_model_info()
    return {
        "step": step,
        **model_info,
        **tokens,
    }


def append_usage_record(
    existing_records: list[dict[str, Any]] | None,
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    return [*(existing_records or []), record]


def summarize_llm_usage(records: list[dict[str, Any]] | None) -> dict[str, Any]:
    items = records or []
    if not items:
        model_info = get_llm_model_info()
        return {
            **model_info,
            "calls": [],
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
        }

    first = items[0]
    total_prompt = sum(int(item.get("prompt_tokens") or 0) for item in items)
    total_completion = sum(int(item.get("completion_tokens") or 0) for item in items)
    total_tokens = sum(int(item.get("total_tokens") or 0) for item in items)

    return {
        "model": first.get("model", get_llm_model_info()["model"]),
        "deployment": first.get("deployment", get_llm_model_info()["deployment"]),
        "provider": first.get("provider", "azure_openai"),
        "calls": items,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_tokens,
    }
