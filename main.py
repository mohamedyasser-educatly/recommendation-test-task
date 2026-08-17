from __future__ import annotations

import argparse
import json
from pathlib import Path

from recommendation.env import load_env_file
from recommendation.graph import graph


DEFAULT_CATALOG = Path(__file__).resolve().parent / "data" / "reference_catalog.json"
DEFAULT_USER = Path(__file__).resolve().parent / "data" / "sample_user_input.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "sample_output.json"


def run(user_input: dict, catalog_path: str | Path) -> dict:
    result = graph.invoke(
        {
            "user_input": user_input,
            "catalog_path": str(catalog_path),
        }
    )
    return result.get("final_output") or {
        "status": result.get("branch_status", "unknown"),
        "message": result.get("error_message"),
    }


def main() -> None:
    load_env_file()

    parser = argparse.ArgumentParser(description="Run the career recommendation graph.")
    parser.add_argument(
        "--user",
        type=Path,
        default=DEFAULT_USER,
        help="Path to user trait profile JSON",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="Path to reference catalog JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the JSON result",
    )
    args = parser.parse_args()

    user_input = json.loads(args.user.read_text(encoding="utf-8"))
    output = run(user_input, args.catalog)

    output_json = json.dumps(output, indent=2, ensure_ascii=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_json, encoding="utf-8")
    print(output_json, end="")


if __name__ == "__main__":
    main()
