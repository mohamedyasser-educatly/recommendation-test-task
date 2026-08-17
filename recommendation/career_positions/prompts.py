from __future__ import annotations

CAREER_POSITIONS_SYSTEM_PROMPT = """\
You are a career path advisor for Educatly.
Given a user profile, development recommendations, and ranked target employers, suggest realistic \
career positions the user can grow into over time.
Ground suggestions in the user's current role, education, segment, and development areas.
For each career position, include example job titles at ranked companies only — infer plausible \
roles that those employers typically offer in the user's field (do not invent company names).
Return up to {max_positions} positions ordered from nearest-term to more aspirational.\
"""

CAREER_POSITIONS_USER_PROMPT = """\
User profile JSON:
{profile_json}

Development report JSON:
{development_json}

Ranked target employers JSON:
{ranked_companies_json}

Allowed company names (use ONLY these in company_examples):
{allowed_company_names}

For each career position provide:
- title: target role the user can become
- career_stage: timeline or seniority (e.g. "2-4 years", "Executive level")
- why_reachable: linked to profile + development areas
- linked_development_areas: names from the development report above
- company_examples: 1-3 entries with company_name, example_position, why_at_this_company\
"""


def build_career_positions_system_prompt(max_positions: int) -> str:
    return CAREER_POSITIONS_SYSTEM_PROMPT.format(max_positions=max_positions)


def build_career_positions_user_prompt(
    profile_json: str,
    development_json: str,
    ranked_companies_json: str,
    allowed_company_names: str,
) -> str:
    return CAREER_POSITIONS_USER_PROMPT.format(
        profile_json=profile_json,
        development_json=development_json,
        ranked_companies_json=ranked_companies_json,
        allowed_company_names=allowed_company_names,
    )
