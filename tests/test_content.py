from __future__ import annotations

import json
from pathlib import Path

import pytest

from wort_content.builder import build_content
from wort_content.validator import ContentValidationError, validate_published, validate_source


ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_source_is_valid() -> None:
    counts = validate_source(ROOT / "data/source")
    assert counts == {
        "coursebooks": 5,
        "modules": 37,
        "words": 2759,
        "exercises": 1,
        "exerciseWords": 39,
    }


def test_build_produces_verified_manifest(tmp_path: Path) -> None:
    output = tmp_path / "published"
    result = build_content(ROOT / "data/source", output)
    assert result["coursebooks"] == 5
    validate_published(output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["catalog"]["sourceCount"] == 6


def test_duplicate_word_id_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    # A focused fixture is clearer here than copying the complete dataset.
    course = source / "coursebooks/test"
    exercise = source / "exercises/test"
    course.mkdir(parents=True)
    exercise.mkdir(parents=True)
    (course / "book.json").write_text(json.dumps({
        "id": "test", "title": "Test", "level": "A1",
        "modules": [{"id": "module0", "title": "Module", "file": "module0.json"}],
    }), encoding="utf-8")
    word = {"id": "same", "type": "noun", "word": "Wort", "translation": {"en": ["word"]}}
    (course / "module0.json").write_text(json.dumps([word, word]), encoding="utf-8")
    (exercise / "exercise.json").write_text(json.dumps({
        "id": "test", "title": "Test", "description": {"en": ["Test"]}, "wordsFile": "words.json",
    }), encoding="utf-8")
    (exercise / "words.json").write_text(json.dumps([{"id": "one"}]), encoding="utf-8")
    with pytest.raises(ContentValidationError, match="duplicate IDs"):
        validate_source(source)

