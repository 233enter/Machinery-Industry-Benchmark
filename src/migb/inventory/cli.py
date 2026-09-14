"""Command-line entry point for D1 and D2 inventory runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .runner import PipelineError, run_d1, run_d2, run_d3
from .safety import SafetyError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the MIGB Minimal Corpus Inventory D1/D2/D3 stage")
    parser.add_argument("--config", required=True, help="environment YAML path")
    parser.add_argument("--stage", choices=("d1", "d2", "d3"), required=True)
    parser.add_argument("--repo-root", default=".", help="repository root for Git provenance")
    parser.add_argument(
        "--prior-run-id",
        action="append",
        help="prior D1/D2 run ID; repeat for D3",
    )
    parser.add_argument("--run-id", help="explicit D3 run ID, required when resuming")
    parser.add_argument("--resume", action="store_true", help="resume an active D3 run")
    parser.add_argument(
        "--target-sample-count",
        type=int,
        default=1000,
        help="D3 target sample count (default: 1000)",
    )
    parser.add_argument(
        "--checkpoint-batch-size",
        type=int,
        default=100,
        help="D3 checkpoint batch size (default: 100)",
    )
    parser.add_argument(
        "--stop-after",
        type=int,
        help="controlled D3 interruption after a completed checkpoint batch",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(Path(args.config))
        if args.stage == "d1":
            if args.prior_run_id or args.run_id or args.resume or args.stop_after:
                raise PipelineError("D1 does not support prior runs or D3-only run controls")
            result = run_d1(config, repo_root=Path(args.repo_root))
        elif args.stage == "d2":
            if not args.prior_run_id or len(args.prior_run_id) != 1:
                raise PipelineError("--stage d2 requires --prior-run-id")
            if args.run_id or args.resume or args.stop_after:
                raise PipelineError("D2 does not support D3-only run controls")
            result = run_d2(
                config,
                prior_run_id=args.prior_run_id[0],
                repo_root=Path(args.repo_root),
            )
        else:
            if not args.prior_run_id or len(args.prior_run_id) < 2:
                raise PipelineError("--stage d3 requires D1 and D2 --prior-run-id values")
            result = run_d3(
                config,
                prior_run_ids=args.prior_run_id,
                repo_root=Path(args.repo_root),
                run_id=args.run_id,
                resume=args.resume,
                target_sample_count=args.target_sample_count,
                checkpoint_batch_size=args.checkpoint_batch_size,
                stop_after=args.stop_after,
            )
    except (ConfigError, PipelineError, SafetyError, OSError) as exc:
        print(f"Inventory stage failed to start or complete safely: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "run_directory": str(result.run_directory),
                "run_status": getattr(result, "run_status", "completed"),
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
