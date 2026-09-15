"""Command-line entry point for the Phase 2 Gate 2B run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from migb.inventory.safety import SafetyError

from .config import Phase2ConfigError, load_phase2_config
from .runner import Phase2Error, run_phase2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run MIGB Phase 2 Gate 2B deterministic sampling and lightweight Evidence"
    )
    parser.add_argument("--config", required=True, help="Phase 2 calibration YAML path")
    parser.add_argument("--repo-root", default=".", help="repository root for Git provenance")
    parser.add_argument("--run-id", help="explicit p2b- run ID; otherwise generate one")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_phase2_config(Path(args.config))
        result = run_phase2(
            config,
            repo_root=Path(args.repo_root),
            run_id=args.run_id,
        )
    except (Phase2ConfigError, Phase2Error, SafetyError, OSError, ValueError) as exc:
        print(f"Phase 2 Gate 2B failed to start or complete safely: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "run_directory": str(result.run_directory),
                "gate2b_verdict": result.gate2b_verdict,
                "artifact_validation": result.artifact_validation,
                "manifest": result.manifest,
                "statistics": result.statistics,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
