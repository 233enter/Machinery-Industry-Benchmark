from __future__ import annotations

from pathlib import Path

import pytest

from migb.phase2.config import Phase2ConfigError, load_phase2_config


def _write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "calibration.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_phase2_config_loads_frozen_defaults(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
input:
  inventory_run_id: full-test
  inventory_root: /data/inventory/runs/full-test
  source_root: /source/cmes
migb_data_root: /data/migb
sampling:
  main_target: 600
  base_quota_per_parent_group: 15
  audit:
    source_quality_exception: all
    text_absent_target: 60
    mixed_text_target: 40
    filename_unmatched_target: 60
evidence:
  page_indices: [0, 1, 2]
  max_extracted_chars: 12000
  worker_count: 4
""",
    )
    config = load_phase2_config(path)
    assert config.sampling.main_target == 600
    assert config.evidence.page_indices == (0, 1, 2)
    assert config.fingerprint() == load_phase2_config(path).fingerprint()


def test_phase2_config_rejects_non_gate2b_page_selection(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
input:
  inventory_run_id: full-test
  inventory_root: /data/inventory/runs/full-test
  source_root: /source/cmes
migb_data_root: /data/migb
evidence:
  page_indices: [0, 2]
""",
    )
    with pytest.raises(Phase2ConfigError, match="exactly \\[0, 1, 2\\]"):
        load_phase2_config(path)


def test_phase2_config_rejects_secret_like_keys(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
input:
  inventory_run_id: full-test
  inventory_root: /data/inventory/runs/full-test
  source_root: /source/cmes
migb_data_root: /data/migb
api_key: should-not-be-here
""",
    )
    with pytest.raises(Phase2ConfigError, match="secret-like"):
        load_phase2_config(path)
