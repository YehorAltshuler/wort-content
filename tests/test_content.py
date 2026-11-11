from __future__ import annotations

import json
from pathlib import Path

import pytest

from wort_content.builder import build_content
from wort_content.validator import ContentValidationError, validate_published, validate_source


ROOT = Path(__file__).resolve().parents[1]


def _source_counts() -> dict[str, int]:
    source = ROOT / "data/source"
    book_paths = sorted((source / "coursebooks").glob("*/book.json"))
    exercise_paths = sorted((source / "exercises").glob("*/exercise.json"))

    modules = [
        (book_path.parent / module["file"])
        for book_path in book_paths
        for module in json.loads(book_path.read_text(encoding="utf-8"))["modules"]
    ]
    exercise_words = [
        exercise_path.parent
        / json.loads(exercise_path.read_text(encoding="utf-8")).get(
            "wordsFile", "words.json"
        )
        for exercise_path in exercise_paths
    ]

    return {
        "coursebooks": len(book_paths),
        "modules": len(modules),
        "words": sum(
            len(json.loads(path.read_text(encoding="utf-8"))) for path in modules
        ),
        "exercises": len(exercise_paths),
        "exerciseWords": sum(
            len(json.loads(path.read_text(encoding="utf-8")))
            for path in exercise_words
        ),
    }


def test_checked_in_source_is_valid() -> None:
    counts = validate_source(ROOT / "data/source")
    assert counts == _source_counts()


def test_build_produces_verified_manifest(tmp_path: Path) -> None:
    output = tmp_path / "published"
    expected_counts = _source_counts()
    result = build_content(ROOT / "data/source", output)
    assert {key: result[key] for key in expected_counts} == expected_counts
    validate_published(output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    expected_source_count = result["coursebooks"] + result["exercises"]
    assert manifest["catalog"]["sourceCount"] == expected_source_count


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

