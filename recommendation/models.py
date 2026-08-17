from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


class HighschoolProfile(BaseModel):
    curriculum: str | None = None
    grade: str | None = None


class UniversityProfile(BaseModel):
    university_name: str | None = None
    area_of_study: list[str] = Field(default_factory=list)
    major: list[str] = Field(default_factory=list)
    degree_level: str | None = None


class ProfessionalProfile(BaseModel):
    university_name: str | None = None
    area_of_study: list[str] = Field(default_factory=list)
    major: list[str] = Field(default_factory=list)
    currently_working: bool | None = None
    current_company: str | None = None
    current_job_title: str | None = None
    highest_level_of_education: str | None = None
    years_of_work_experience: int | None = None
    career_intent: str | None = None


class UserProfile(BaseModel):
    age: int | None = None
    country: str | None = None
    highschool: HighschoolProfile | None = None
    university: UniversityProfile | None = None
    professional: ProfessionalProfile | None = None


class UserInput(BaseModel):
    user_id: int
    user_segment: str
    user_profile: UserProfile

    @field_validator("user_segment")
    @classmethod
    def segment_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must be a non-empty string")
        return cleaned


class CompanyItem(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    sector: str = Field(min_length=1)
    regions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    fit_segments: list[str] = Field(default_factory=list)


class ReferenceCatalog(BaseModel):
    companies: list[CompanyItem] = Field(min_length=1)


def format_validation_errors(exc: ValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        parts.append(f"{location}: {error['msg']}")
    return "; ".join(parts)


def parse_user_input(raw: Any) -> UserInput:
    return UserInput.model_validate(raw)


def parse_reference_catalog(raw: Any) -> ReferenceCatalog:
    return ReferenceCatalog.model_validate(raw)
