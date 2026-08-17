from typing import Literal

MAX_COMPANIES = 5
MAX_COMPANY_CANDIDATES = 10
MIN_COMPANY_FIT_SCORE = 60
MAX_DEVELOPMENT_AREAS = 3
MAX_CAREER_POSITIONS = 4
MAX_VALIDATION_RETRIES = 3

RecoveryTarget = Literal[
    "rank_companies",
    "prepare_development_context",
    "llm_career_positions",
]
