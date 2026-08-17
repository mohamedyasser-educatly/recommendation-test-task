from __future__ import annotations

import json
from typing import Any

from recommendation.career_positions.constants import MAX_CAREER_POSITIONS
from recommendation.career_positions.prompts import (
    build_career_positions_system_prompt,
    build_career_positions_user_prompt,
)
from recommendation.llm.client import invoke_structured
from recommendation.llm.errors import RecommendationLLMError
from recommendation.schemas.career_positions import CareerPositionsBranchOutput


def generate_career_positions(
    user_input: dict[str, Any],
    development_areas: list[dict[str, Any]],
    ranked_companies: list[dict[str, Any]],
    *,
    max_positions: int = MAX_CAREER_POSITIONS,
) -> list[dict[str, Any]]:
    allowed_names = [company["name"] for company in ranked_companies]
    if not allowed_names:
        raise RecommendationLLMError(
            "Cannot generate career positions without ranked companies."
        )

    profile_json = json.dumps(user_input, indent=2, ensure_ascii=False)
    development_json = json.dumps(development_areas, indent=2, ensure_ascii=False)
    ranked_companies_json = json.dumps(
        [
            {
                "rank": company.get("rank"),
                "name": company["name"],
                "sector": company["sector"],
                "why_recommended": company.get("why_recommended"),
            }
            for company in ranked_companies
        ],
        indent=2,
        ensure_ascii=False,
    )
    allowed_company_names = ", ".join(allowed_names)

    result = invoke_structured(
        CareerPositionsBranchOutput,
        system_prompt=build_career_positions_system_prompt(max_positions),
        user_prompt=build_career_positions_user_prompt(
            profile_json,
            development_json,
            ranked_companies_json,
            allowed_company_names,
        ),
        error_prefix="LLM career positions generation failed",
    )

    positions = [
        {
            "rank": index,
            **position.model_dump(),
        }
        for index, position in enumerate(result.career_positions[:max_positions], start=1)
    ]
    if not positions:
        raise RecommendationLLMError("LLM career positions returned an empty list.")
    return positions
