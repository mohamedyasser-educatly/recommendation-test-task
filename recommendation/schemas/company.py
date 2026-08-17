from pydantic import BaseModel, Field

from recommendation.constants import MAX_COMPANY_CANDIDATES, MIN_COMPANY_FIT_SCORE


class RankedCompanyPick(BaseModel):
    id: str = Field(description="Exact company id from the reference catalog.")
    score: float = Field(
        ge=0,
        le=100,
        description=(
            f"LLM fit score from 0-100. Only companies strictly above "
            f"{MIN_COMPANY_FIT_SCORE}% are kept."
        ),
    )
    why_recommended: str = Field(description="Why this employer fits the user profile.")


class CompanyRankingOutput(BaseModel):
    companies: list[RankedCompanyPick] = Field(
        min_length=1,
        max_length=MAX_COMPANY_CANDIDATES,
        description=(
            "Employers evaluated best-to-worst from the reference catalog only, "
            "each with a fit score."
        ),
    )
