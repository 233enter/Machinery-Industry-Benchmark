from __future__ import annotations

from pathlib import Path

from migb.inventory.config import load_config


def test_xuelangyun_environment_config_injects_paths() -> None:
    repository_root = Path(__file__).parents[1]
    config = load_config(repository_root / "configs/environments/xuelangyun.yaml")

    assert config.source_roots[0].source_root_id == "cmes_journal"
    assert str(config.source_roots[0].path) == "/mnt/data_nfs/dataset/original/cmes/journal"
    assert str(config.migb_data_root) == "/data/suzhe/migb"
    assert config.inventory.worker_count == 4
    assert config.inventory.text_page_char_threshold == 50
