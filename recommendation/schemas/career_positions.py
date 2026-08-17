from pydantic import BaseModel, Field

from recommendation.constants import MAX_CAREER_POSITIONS


class CompanyRoleExample(BaseModel):
    company_name: str = Field(description="Employer name — must be from the ranked companies list.")
    example_position: str = Field(
        description="A realistic job title at this company the user could grow into."
    )
    why_at_this_company: str = Field(
        description="Why this role at this company fits the user's trajectory."
    )


class CareerPositionOutput(BaseModel):
    title: str = Field(description="Target career position title the user can grow into.")
    career_stage: str = Field(
        description="Typical timeline or seniority stage, e.g. '3-5 years' or 'Senior level'."
    )
    why_reachable: str = Field(
        description="Why this position is reachable given the user's profile and development path."
    )
    linked_development_areas: list[str] = Field(
        min_length=1,
        description="Development areas from the report that support this career move.",
    )
    company_examples: list[CompanyRoleExample] = Field(
        min_length=1,
        description="Example roles at ranked employers illustrating this career path.",
    )


class CareerPositionsBranchOutput(BaseModel):
    career_positions: list[CareerPositionOutput] = Field(
        min_length=1,
        max_length=MAX_CAREER_POSITIONS,
        description="Career positions ordered from nearest to most aspirational.",
    )
