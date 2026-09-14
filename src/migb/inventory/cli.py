"""Command-line entry point for the D1 Smoke Test."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .runner import PipelineError, run_d1
from .safety import SafetyError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the MIGB Minimal Corpus Inventory D1 Smoke Test")
    parser.add_argument("--config", required=True, help="environment YAML path")
    parser.add_argument("--stage", choices=("d1",), required=True)
    parser.add_argument("--repo-root", default=".", help="repository root for Git provenance")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(Path(args.config))
        result = run_d1(config, repo_root=Path(args.repo_root))
    except (ConfigError, PipelineError, SafetyError, OSError) as exc:
        print(f"D1 failed to start or complete safely: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "run_directory": str(result.run_directory),
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
