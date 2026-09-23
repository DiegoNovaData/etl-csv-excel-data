import json
from pathlib import Path

import pytest
import yaml

from src.load.load_products import run


def _write_config(tmp_path: Path, processed_dir: Path, output_dir: Path) -> Path:
    config = {
        "paths": {
            "raw_data_dir": str(tmp_path / "raw"),
            "processed_data_dir": str(processed_dir),
            "output_data_dir": str(output_dir),
        }
    }
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)
    return config_path


def _write_processed_tables(processed_dir: Path) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / "products.csv").write_text("product_id,title\n1,Foo\n2,Bar\n", encoding="utf-8")
    (processed_dir / "product_reviews.csv").write_text("review_id,product_id\n1,1\n", encoding="utf-8")
    (processed_dir / "product_tags.csv").write_text("product_id,tag\n1,foo\n", encoding="utf-8")
    (processed_dir / "product_images.csv").write_text("product_id,image_url\n1,http://x\n", encoding="utf-8")


def test_run_copies_tables_and_writes_manifest(tmp_path: Path):
    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "output"
    _write_processed_tables(processed_dir)
    config_path = _write_config(tmp_path, processed_dir, output_dir)

    result_dir = run(config_path)

    assert result_dir == output_dir
    assert (output_dir / "products.csv").read_text(encoding="utf-8") == (
        processed_dir / "products.csv"
    ).read_text(encoding="utf-8")

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["tables"]["products"]["row_count"] == 2
    assert manifest["tables"]["product_reviews"]["row_count"] == 1
    assert "loaded_at" in manifest


def test_run_raises_if_processed_table_missing(tmp_path: Path):
    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "output"
    processed_dir.mkdir(parents=True)
    config_path = _write_config(tmp_path, processed_dir, output_dir)

    with pytest.raises(FileNotFoundError):
        run(config_path)
