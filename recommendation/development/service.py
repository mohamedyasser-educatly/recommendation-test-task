from __future__ import annotations

import json
from typing import Any

from recommendation.development.constants import MAX_DEVELOPMENT_AREAS
from recommendation.development.prompts import (
    build_development_report_system_prompt,
    build_development_report_user_prompt,
)
from recommendation.llm.client import invoke_structured
from recommendation.llm.errors import RecommendationLLMError
from recommendation.schemas.development import DevelopmentBranchOutput


def generate_development_report(
    user_input: dict[str, Any],
    allowed_company_names: list[str],
    *,
    max_areas: int = MAX_DEVELOPMENT_AREAS,
) -> tuple[DevelopmentBranchOutput, dict[str, Any]]:
    allowed_names_text = (
        ", ".join(allowed_company_names)
        if allowed_company_names
        else "(none — do not mention employers)"
    )
    profile_json = json.dumps(user_input, indent=2, ensure_ascii=False)

    invoke_result = invoke_structured(
        DevelopmentBranchOutput,
        system_prompt=build_development_report_system_prompt(max_areas),
        user_prompt=build_development_report_user_prompt(
            profile_json,
            max_areas=max_areas,
            allowed_names_text=allowed_names_text,
        ),
        step="llm_development_report",
        error_prefix="LLM development report generation failed",
    )

    trimmed = DevelopmentBranchOutput(
        development_areas=invoke_result.parsed.development_areas[:max_areas],
        narrative=invoke_result.parsed.narrative.strip(),
    )
    if not trimmed.narrative:
        raise RecommendationLLMError("LLM returned an empty narrative.")
    return trimmed, invoke_result.usage
