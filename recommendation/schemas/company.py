from pydantic import BaseModel, Field

from recommendation.constants import MAX_COMPANIES


class RankedCompanyPick(BaseModel):
    id: str = Field(description="Exact company id from the reference catalog.")
    why_recommended: str = Field(description="Why this employer fits the user profile.")


class CompanyRankingOutput(BaseModel):
    companies: list[RankedCompanyPick] = Field(
        min_length=1,
        max_length=MAX_COMPANIES,
        description="Employers ranked best-to-worst from the reference catalog only.",
    )
