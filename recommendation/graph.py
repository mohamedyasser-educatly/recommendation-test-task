from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from recommendation.constants import MAX_VALIDATION_RETRIES
from recommendation.nodes import (
    assemble_success,
    handle_catalog_error,
    handle_validation_failure,
    llm_career_positions,
    llm_development_report,
    load_catalog,
    prepare_development_context,
    rank_companies,
    recover_validation,
    validate_output,
    validate_user_input,
)
from recommendation.state import GraphState


def _route_after_input(state: GraphState) -> str:
    if state.get("branch_status") == "input_error":
        return END
    return "load_catalog"


def _route_after_catalog(state: GraphState) -> str:
    if state.get("catalog_status") != "ok":
        return "handle_catalog_error"
    return "rank_companies"


def _route_after_validation(state: GraphState) -> str:
    if state.get("validation_passed"):
        return "assemble_success"
    retry_count = state.get("validation_retry_count") or 0
    if retry_count < MAX_VALIDATION_RETRIES:
        return "recover_validation"
    return "handle_validation_failure"


def _route_after_recovery(state: GraphState) -> str:
    target = state.get("recovery_target")
    if target == "rank_companies":
        return "rank_companies"
    if target == "llm_career_positions":
        return "llm_career_positions"
    return "prepare_development_context"


def build_graph():
    """Graph: Pydantic gates, LLM pipeline, career positions, validator with recovery retries."""
    builder = StateGraph(GraphState)

    builder.add_node("validate_user_input", validate_user_input)
    builder.add_node("load_catalog", load_catalog)
    builder.add_node("rank_companies", rank_companies)
    builder.add_node("prepare_development_context", prepare_development_context)
    builder.add_node("llm_development_report", llm_development_report)
    builder.add_node("llm_career_positions", llm_career_positions)
    builder.add_node("validate_output", validate_output)
    builder.add_node("recover_validation", recover_validation)
    builder.add_node("assemble_success", assemble_success)
    builder.add_node("handle_catalog_error", handle_catalog_error)
    builder.add_node("handle_validation_failure", handle_validation_failure)

    builder.add_edge(START, "validate_user_input")
    builder.add_conditional_edges(
        "validate_user_input",
        _route_after_input,
        {END: END, "load_catalog": "load_catalog"},
    )
    builder.add_conditional_edges(
        "load_catalog",
        _route_after_catalog,
        {
            "handle_catalog_error": "handle_catalog_error",
            "rank_companies": "rank_companies",
        },
    )
    builder.add_edge("rank_companies", "prepare_development_context")
    builder.add_edge("prepare_development_context", "llm_development_report")
    builder.add_edge("llm_development_report", "llm_career_positions")
    builder.add_edge("llm_career_positions", "validate_output")

    builder.add_conditional_edges(
        "validate_output",
        _route_after_validation,
        {
            "assemble_success": "assemble_success",
            "recover_validation": "recover_validation",
            "handle_validation_failure": "handle_validation_failure",
        },
    )
    builder.add_conditional_edges(
        "recover_validation",
        _route_after_recovery,
        {
            "rank_companies": "rank_companies",
            "prepare_development_context": "prepare_development_context",
            "llm_career_positions": "llm_career_positions",
        },
    )

    builder.add_edge("assemble_success", END)
    builder.add_edge("handle_catalog_error", END)
    builder.add_edge("handle_validation_failure", END)

    return builder.compile()


graph = build_graph()
