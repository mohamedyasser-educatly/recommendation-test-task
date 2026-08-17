from __future__ import annotations

DEVELOPMENT_REPORT_SYSTEM_PROMPT = """\
You are a career development advisor for Educatly.
Given a user trait profile, produce personalized development recommendations.
Do NOT copy from any external catalog — infer areas from the profile alone.
Be specific to the user's segment, education, role, country, and experience.
Return exactly up to {max_areas} development areas, ordered by relevance.\
"""

DEVELOPMENT_REPORT_USER_PROMPT = """\
User profile JSON:
{profile_json}

Produce:
1. Up to {max_areas} development areas with: area_of_developing, why, skills_to_acquire, topics_to_learn.
2. A short narrative (2-4 sentences) summarizing growth priorities.

Narrative rules:
- You may ONLY mention these employer names if you reference companies: {allowed_names_text}
- Do not mention any other company or employer names.
- Focus the narrative on development priorities; company mentions are optional.\
"""


def build_development_report_system_prompt(max_areas: int) -> str:
    return DEVELOPMENT_REPORT_SYSTEM_PROMPT.format(max_areas=max_areas)


def build_development_report_user_prompt(
    profile_json: str,
    *,
    max_areas: int,
    allowed_names_text: str,
) -> str:
    return DEVELOPMENT_REPORT_USER_PROMPT.format(
        profile_json=profile_json,
        max_areas=max_areas,
        allowed_names_text=allowed_names_text,
    )
