from pydantic import BaseModel, Field

from recommendation.constants import MAX_DEVELOPMENT_AREAS


class DevelopmentAreaOutput(BaseModel):
    area_of_developing: str = Field(description="Name of the skill or growth area.")
    why: str = Field(description="Why this area matters for this specific user.")
    skills_to_acquire: list[str] = Field(min_length=1, description="Concrete skills to acquire.")
    topics_to_learn: list[str] = Field(min_length=1, description="Topics to learn.")


class DevelopmentBranchOutput(BaseModel):
    development_areas: list[DevelopmentAreaOutput] = Field(
        min_length=1,
        max_length=MAX_DEVELOPMENT_AREAS,
        description="Ranked development recommendations tailored to the user profile.",
    )
    narrative: str = Field(
        description=(
            "Short career narrative for the user. If mentioning employers, "
            "use ONLY the allowed company names provided in the prompt."
        )
    )
