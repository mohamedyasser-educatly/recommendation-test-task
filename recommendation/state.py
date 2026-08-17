from __future__ import annotations

from typing import Any, Literal, TypedDict

from recommendation.constants import RecoveryTarget


CatalogStatus = Literal["ok", "empty", "malformed", "missing"]
BranchStatus = Literal[
    "pending",
    "success",
    "input_error",
    "catalog_error",
    "validation_failed",
]


class RankedCompany(TypedDict):
    rank: int
    id: str
    name: str
    sector: str
    why_recommended: str


class DevelopmentArea(TypedDict):
    rank: int
    area_of_developing: str
    why: str
    skills_to_acquire: list[str]
    topics_to_learn: list[str]


class CompanyRoleExample(TypedDict):
    company_name: str
    example_position: str
    why_at_this_company: str


class CareerPosition(TypedDict):
    rank: int
    title: str
    career_stage: str
    why_reachable: str
    linked_development_areas: list[str]
    company_examples: list[CompanyRoleExample]


class GraphState(TypedDict, total=False):
    user_input: dict[str, Any]
    catalog_path: str
    catalog: dict[str, Any]
    catalog_status: CatalogStatus
    catalog_error: str | None

    ranked_companies: list[RankedCompany]
    allowed_company_names: list[str]
    development_areas: list[DevelopmentArea]
    narrative: str
    career_positions: list[CareerPosition]

    validation_passed: bool
    validation_errors: list[str]
    branch_status: BranchStatus
    final_output: dict[str, Any] | None
    error_message: str | None
    development_branch_error: str | None
    company_branch_error: str | None
    career_positions_branch_error: str | None
    validation_retry_count: int
    recovery_target: RecoveryTarget
    llm_usage_records: list[dict[str, Any]]
