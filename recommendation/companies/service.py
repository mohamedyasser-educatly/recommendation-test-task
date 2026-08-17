from __future__ import annotations

import json
from typing import Any

from recommendation.companies.constants import MAX_COMPANIES
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
) -> list[dict[str, Any]]:
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

    result = invoke_structured(
        CompanyRankingOutput,
        system_prompt=build_company_ranking_system_prompt(max_companies),
        user_prompt=build_company_ranking_user_prompt(profile_json, catalog_json),
        error_prefix="LLM company ranking failed",
    )

    return _map_ranking_to_catalog(result, catalog_companies, max_companies)


def _map_ranking_to_catalog(
    result: CompanyRankingOutput,
    catalog_companies: list[dict[str, Any]],
    max_companies: int,
) -> list[dict[str, Any]]:
    catalog_by_id = {company["id"]: company for company in catalog_companies}
    ranked: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for pick in result.companies[:max_companies]:
        if pick.id in seen_ids:
            continue
        catalog_company = catalog_by_id.get(pick.id)
        if catalog_company is None:
            raise RecommendationLLMError(
                f"LLM selected unknown catalog company id: {pick.id}"
            )
        seen_ids.add(pick.id)
        ranked.append(
            {
                "rank": len(ranked) + 1,
                "id": catalog_company["id"],
                "name": catalog_company["name"],
                "sector": catalog_company["sector"],
                "why_recommended": pick.why_recommended.strip(),
            }
        )

    if not ranked:
        raise RecommendationLLMError("LLM company ranking returned no valid catalog companies.")
    return ranked
