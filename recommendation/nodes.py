from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from recommendation.career_positions import generate_career_positions
from recommendation.companies import MAX_COMPANIES, rank_companies_from_catalog
from recommendation.development import MAX_DEVELOPMENT_AREAS, generate_development_report
from recommendation.llm.errors import DevelopmentLLMError
from recommendation.models import format_validation_errors, parse_reference_catalog, parse_user_input
from recommendation.constants import RecoveryTarget
from recommendation.state import GraphState


def validate_user_input(state: GraphState) -> GraphState:
    """Deterministic input gate — Pydantic schema validation, no LLM."""
    try:
        validated = parse_user_input(state.get("user_input"))
    except ValidationError as exc:
        message = format_validation_errors(exc)
        return _input_failure(message)

    return {
        "user_input": validated.model_dump(),
        "branch_status": "pending",
        "validation_errors": [],
        "validation_retry_count": 0,
    }


def load_catalog(state: GraphState) -> GraphState:
    """Deterministic catalog gate — JSON load + Pydantic schema validation, no LLM."""
    catalog_path = state.get("catalog_path")
    if not catalog_path:
        return _catalog_failure("missing", "No catalog_path provided in graph input.")

    path = Path(catalog_path)
    if not path.exists():
        return _catalog_failure("missing", f"Catalog file not found: {catalog_path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _catalog_failure("malformed", f"Catalog JSON is malformed: {exc.msg}")

    try:
        catalog = parse_reference_catalog(raw)
    except ValidationError as exc:
        message = format_validation_errors(exc)
        status = "empty" if "companies" in message and "at least 1" in message.lower() else "malformed"
        return _catalog_failure(status, message)

    return {
        "catalog": catalog.model_dump(),
        "catalog_status": "ok",
        "catalog_error": None,
    }


def rank_companies(state: GraphState) -> GraphState:
    """LLM graph node — rank employers constrained to the reference catalog."""
    try:
        ranked = rank_companies_from_catalog(
            state["user_input"],
            state["catalog"]["companies"],
            max_companies=MAX_COMPANIES,
        )
    except DevelopmentLLMError as exc:
        return {
            "ranked_companies": [],
            "company_branch_error": str(exc),
        }

    return {
        "ranked_companies": ranked,
        "company_branch_error": None,
    }


def prepare_development_context(state: GraphState) -> GraphState:
    """Derive allowed employer names from branch A ranked output for narrative constraint."""
    ranked = state.get("ranked_companies") or []
    return {"allowed_company_names": [company["name"] for company in ranked]}


def llm_development_report(state: GraphState) -> GraphState:
    """LLM graph node — generates development report and narrative from user profile."""
    try:
        llm_result = generate_development_report(
            state["user_input"],
            state.get("allowed_company_names") or [],
            max_areas=MAX_DEVELOPMENT_AREAS,
        )
    except DevelopmentLLMError as exc:
        return {
            "development_areas": [],
            "narrative": "",
            "development_branch_error": str(exc),
        }

    development_areas = [
        {"rank": index, **area.model_dump()}
        for index, area in enumerate(llm_result.development_areas, start=1)
    ]
    return {
        "development_areas": development_areas,
        "narrative": llm_result.narrative,
        "development_branch_error": None,
    }


def llm_career_positions(state: GraphState) -> GraphState:
    """LLM graph node — career positions grounded in profile, development report, and ranked employers."""
    try:
        positions = generate_career_positions(
            state["user_input"],
            state.get("development_areas") or [],
            state.get("ranked_companies") or [],
        )
    except DevelopmentLLMError as exc:
        return {
            "career_positions": [],
            "career_positions_branch_error": str(exc),
        }

    return {
        "career_positions": positions,
        "career_positions_branch_error": None,
    }


def validate_output(state: GraphState) -> GraphState:
    errors: list[str] = []

    ranked = state.get("ranked_companies")
    areas = state.get("development_areas")
    narrative = state.get("narrative")
    career_positions = state.get("career_positions")

    if ranked is None or areas is None or narrative is None or career_positions is None:
        return {}

    branch_error = state.get("development_branch_error")
    if branch_error:
        errors.append(f"Development branch failed: {branch_error}")

    career_error = state.get("career_positions_branch_error")
    if career_error:
        errors.append(f"Career positions branch failed: {career_error}")

    if not career_positions and not career_error:
        errors.append("Career positions branch produced no positions.")

    company_error = state.get("company_branch_error")
    if company_error:
        errors.append(f"Company ranking branch failed: {company_error}")

    if not areas and not branch_error:
        errors.append("Development report branch produced no areas.")

    allowed_names = {company["name"].lower() for company in ranked}
    catalog_names = [
        company["name"]
        for company in state.get("catalog", {}).get("companies", [])
    ]
    mentioned = _extract_company_mentions(narrative, catalog_names)
    unknown = [name for name in mentioned if name.lower() not in allowed_names]
    if unknown:
        errors.append(
            "Narrative references companies not present in ranked output: "
            + ", ".join(sorted(set(unknown)))
        )

    for position in career_positions:
        for field in (
            "title",
            "career_stage",
            "why_reachable",
            "linked_development_areas",
            "company_examples",
        ):
            if field not in position:
                errors.append(f"Career position missing required field '{field}'.")
        for example in position.get("company_examples") or []:
            company_name = example.get("company_name", "")
            if company_name.lower() not in allowed_names:
                errors.append(
                    f"Career position references unknown company: {company_name}"
                )
            for field in ("company_name", "example_position", "why_at_this_company"):
                if field not in example:
                    errors.append(f"Company role example missing required field '{field}'.")

    for company in ranked:
        for field in ("id", "name", "sector", "why_recommended", "rank"):
            if field not in company:
                errors.append(f"Ranked company missing required field '{field}'.")

    for area in areas:
        for field in ("area_of_developing", "why", "skills_to_acquire", "topics_to_learn"):
            if field not in area:
                errors.append(f"Development area missing required field '{field}'.")

    if not ranked:
        errors.append("Ranked companies list is empty despite a valid catalog.")

    return {
        "validation_passed": not errors,
        "validation_errors": errors,
    }


def assemble_success(state: GraphState) -> GraphState:
    user_input = state["user_input"]
    return {
        "branch_status": "success",
        "final_output": {
            "status": "success",
            "user_id": user_input.get("user_id"),
            "user_segment": user_input.get("user_segment"),
            "recommended_companies": [
                {
                    "rank": company["rank"],
                    "name": company["name"],
                    "sector": company["sector"],
                    "why_recommended": company["why_recommended"],
                }
                for company in state.get("ranked_companies") or []
            ],
            "development_report": [
                {
                    "area_of_developing": area["area_of_developing"],
                    "why": area["why"],
                    "skills_to_acquire": area["skills_to_acquire"],
                    "topics_to_learn": area["topics_to_learn"],
                }
                for area in state.get("development_areas") or []
            ],
            "narrative": state.get("narrative", ""),
            "career_positions": _format_career_positions(state.get("career_positions") or []),
        },
    }


def handle_catalog_error(state: GraphState) -> GraphState:
    user_input = state.get("user_input") or {}
    message = state.get("catalog_error") or "Reference catalog could not be loaded."
    return {
        "branch_status": "catalog_error",
        "error_message": message,
        "final_output": {
            "status": "catalog_error",
            "catalog_status": state.get("catalog_status"),
            "message": message,
            "user_id": user_input.get("user_id"),
            "recommended_companies": [],
            "development_report": [],
            "narrative": "",
            "career_positions": [],
        },
    }


def recover_validation(state: GraphState) -> GraphState:
    """Increment retry counter, pick recovery path, and clear stale validation flags."""
    retry_count = (state.get("validation_retry_count") or 0) + 1
    target = _determine_recovery_target(state)
    updates: GraphState = {
        "validation_retry_count": retry_count,
        "recovery_target": target,
        "validation_passed": False,
        "validation_errors": [],
    }
    if target == "rank_companies":
        updates["ranked_companies"] = []
        updates["allowed_company_names"] = []
        updates["development_areas"] = []
        updates["narrative"] = ""
        updates["career_positions"] = []
        updates["company_branch_error"] = None
        updates["development_branch_error"] = None
        updates["career_positions_branch_error"] = None
    elif target == "prepare_development_context":
        updates["development_areas"] = []
        updates["narrative"] = ""
        updates["career_positions"] = []
        updates["development_branch_error"] = None
        updates["career_positions_branch_error"] = None
    else:
        updates["career_positions"] = []
        updates["career_positions_branch_error"] = None
    return updates


def handle_validation_failure(state: GraphState) -> GraphState:
    user_input = state.get("user_input") or {}
    errors = state.get("validation_errors") or ["Unknown validation failure."]
    message = "; ".join(errors)
    return {
        "branch_status": "validation_failed",
        "error_message": message,
        "final_output": {
            "status": "validation_failed",
            "message": message,
            "validation_errors": errors,
            "validation_retry_count": state.get("validation_retry_count") or 0,
            "retries_exhausted": True,
            "user_id": user_input.get("user_id"),
            "recommended_companies": [
                {
                    "rank": company.get("rank"),
                    "name": company.get("name"),
                    "sector": company.get("sector"),
                    "why_recommended": company.get("why_recommended"),
                }
                for company in (state.get("ranked_companies") or [])
            ],
            "development_report": [
                {
                    "area_of_developing": area.get("area_of_developing"),
                    "why": area.get("why"),
                    "skills_to_acquire": area.get("skills_to_acquire"),
                    "topics_to_learn": area.get("topics_to_learn"),
                }
                for area in (state.get("development_areas") or [])
            ],
            "narrative": state.get("narrative", ""),
            "career_positions": _format_career_positions(state.get("career_positions") or []),
        },
    }


def _input_failure(message: str) -> GraphState:
    return {
        "branch_status": "input_error",
        "error_message": message,
        "final_output": {
            "status": "input_error",
            "message": message,
            "recommended_companies": [],
            "development_report": [],
            "narrative": "",
            "career_positions": [],
        },
    }


def _catalog_failure(status: str, message: str) -> GraphState:
    return {
        "catalog_status": status,
        "catalog_error": message,
        "branch_status": "catalog_error",
        "error_message": message,
    }



def _determine_recovery_target(state: GraphState) -> RecoveryTarget:
    if state.get("company_branch_error"):
        return "rank_companies"
    if not state.get("ranked_companies"):
        return "rank_companies"

    for error in state.get("validation_errors") or []:
        lowered = error.lower()
        if "company ranking" in lowered or "ranked compan" in lowered:
            return "rank_companies"
        if "career position" in lowered:
            return "llm_career_positions"

    if state.get("career_positions_branch_error"):
        return "llm_career_positions"
    if state.get("development_branch_error"):
        return "prepare_development_context"

    return "llm_career_positions"


def _format_career_positions(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": position.get("rank"),
            "title": position.get("title"),
            "career_stage": position.get("career_stage"),
            "why_reachable": position.get("why_reachable"),
            "linked_development_areas": position.get("linked_development_areas"),
            "company_examples": [
                {
                    "company_name": example.get("company_name"),
                    "example_position": example.get("example_position"),
                    "why_at_this_company": example.get("why_at_this_company"),
                }
                for example in (position.get("company_examples") or [])
            ],
        }
        for position in positions
    ]


def _extract_company_mentions(narrative: str, catalog_names: list[str]) -> list[str]:
    mentioned: list[str] = []
    lowered = narrative.lower()
    for name in sorted(catalog_names, key=len, reverse=True):
        pattern = rf"\b{re.escape(name)}\b"
        if re.search(pattern, narrative, flags=re.IGNORECASE) or name.lower() in lowered:
            mentioned.append(name)
    return mentioned
