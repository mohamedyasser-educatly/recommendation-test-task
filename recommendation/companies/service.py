from __future__ import annotations

import json
from typing import Any

from recommendation.companies.constants import (
    MAX_COMPANIES,
    MAX_COMPANY_CANDIDATES,
    MIN_COMPANY_FIT_SCORE,
)
from recommendation.companies.prompts import (
    build_company_ranking_system_prompt,
    build_company_ranking_user_prompt,
)
from recommendation.llm.client import invoke_structured
from recommendation.llm.errors import RecommendationLLMError
from recommendation.schemas.company import CompanyRankingOutput


def rank_companies_from_catalog(
    user_input: dict[str, Any],
    catalog_companies: list[dict[str, Any]],
    *,
    max_companies: int = MAX_COMPANIES,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    profile_json = json.dumps(user_input, indent=2, ensure_ascii=False)
    catalog_json = json.dumps(
        [
            {
                "id": company["id"],
                "name": company["name"],
                "sector": company["sector"],
                "regions": company.get("regions") or [],
                "tags": company.get("tags") or [],
                "fit_segments": company.get("fit_segments") or [],
            }
            for company in catalog_companies
        ],
        indent=2,
        ensure_ascii=False,
    )

    invoke_result = invoke_structured(
        CompanyRankingOutput,
        system_prompt=build_company_ranking_system_prompt(MAX_COMPANY_CANDIDATES),
        user_prompt=build_company_ranking_user_prompt(profile_json, catalog_json),
        step="rank_companies",
        error_prefix="LLM company ranking failed",
    )

    ranked = _map_ranking_to_catalog(
        invoke_result.parsed,
        catalog_companies,
        max_companies=max_companies,
        min_score=MIN_COMPANY_FIT_SCORE,
    )
    return ranked, invoke_result.usage


def _map_ranking_to_catalog(
    result: CompanyRankingOutput,
    catalog_companies: list[dict[str, Any]],
    max_companies: int,
    min_score: float,
) -> list[dict[str, Any]]:
    catalog_by_id = {company["id"]: company for company in catalog_companies}
    seen_ids: set[str] = set()
    qualified: list[dict[str, Any]] = []

    for pick in sorted(result.companies, key=lambda item: item.score, reverse=True):
        if pick.id in seen_ids:
            continue
        if pick.score <= min_score:
            continue
        catalog_company = catalog_by_id.get(pick.id)
        if catalog_company is None:
            raise RecommendationLLMError(
                f"LLM selected unknown catalog company id: {pick.id}"
            )
        seen_ids.add(pick.id)
        qualified.append(
            {
                "id": catalog_company["id"],
                "name": catalog_company["name"],
                "sector": catalog_company["sector"],
                "score": round(pick.score, 1),
                "why_recommended": pick.why_recommended.strip(),
            }
        )

    ranked = [
        {**company, "rank": index}
        for index, company in enumerate(qualified[:max_companies], start=1)
    ]

    if not ranked:
        raise RecommendationLLMError(
            f"No catalog companies scored above {min_score}% for this user profile."
        )
    return ranked
