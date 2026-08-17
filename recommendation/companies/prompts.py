from __future__ import annotations

COMPANY_RANKING_SYSTEM_PROMPT = """\
You are a career matching advisor for Educatly.
Given a user trait profile and a reference employer catalog, rank the best-fit employers.
You MUST choose only companies present in the catalog — use their exact `id` values.
Do not invent employers. Be specific to the user's segment, education, role, country, and experience.
Return exactly up to {max_companies} companies, ordered from best to worst fit.\
"""

COMPANY_RANKING_USER_PROMPT = """\
User profile JSON:
{profile_json}

Reference employer catalog JSON:
{catalog_json}

For each selected company return:
- id: exact catalog id
- why_recommended: 1-3 sentences explaining the fit for this user\
"""


def build_company_ranking_system_prompt(max_companies: int) -> str:
    return COMPANY_RANKING_SYSTEM_PROMPT.format(max_companies=max_companies)


def build_company_ranking_user_prompt(profile_json: str, catalog_json: str) -> str:
    return COMPANY_RANKING_USER_PROMPT.format(
        profile_json=profile_json,
        catalog_json=catalog_json,
    )
