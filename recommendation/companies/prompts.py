from __future__ import annotations

COMPANY_RANKING_SYSTEM_PROMPT = """\
You are a career matching advisor for Educatly.
Given a user trait profile and a reference employer catalog, evaluate employer fit.
You MUST choose only companies present in the catalog — use their exact `id` values.
Do not invent employers. Be specific to the user's segment, education, role, country, and experience.

For each company, assign a fit score from 0 to 100 (integer or one decimal):
- 90-100: exceptional fit
- 75-89: strong fit
- 61-74: good fit
- 41-60: partial fit
- 0-40: weak fit

Return exactly up to {max_candidates} evaluated companies, ordered from highest to lowest score.\
"""

COMPANY_RANKING_USER_PROMPT = """\
User profile JSON:
{profile_json}

Reference employer catalog JSON:
{catalog_json}

For each selected company return:
- id: exact catalog id
- score: fit score from 0-100 based on your evaluation
- why_recommended: 1-3 sentences explaining the fit and why you gave this score\
"""


def build_company_ranking_system_prompt(max_candidates: int) -> str:
    return COMPANY_RANKING_SYSTEM_PROMPT.format(max_candidates=max_candidates)


def build_company_ranking_user_prompt(profile_json: str, catalog_json: str) -> str:
    return COMPANY_RANKING_USER_PROMPT.format(
        profile_json=profile_json,
        catalog_json=catalog_json,
    )
