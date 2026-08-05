from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .util import read_json, sha256_file


class ContentValidationError(ValueError):
    pass


def _unique_ids(items: list[dict[str, Any]], context: str) -> None:
    ids = [item.get("id") for item in items]
    missing = [index for index, item_id in enumerate(ids) if not item_id]
    duplicates = [item_id for item_id, count in Counter(ids).items() if count > 1]
    if missing:
        raise ContentValidationError(f"{context}: missing IDs at {missing[:10]}")
    if duplicates:
        raise ContentValidationError(f"{context}: duplicate IDs {duplicates[:10]}")


def validate_source(source: Path) -> dict[str, int]:
    course_root = source / "coursebooks"
    exercise_root = source / "exercises"
    books = sorted(course_root.glob("*/book.json"))
    exercises = sorted(exercise_root.glob("*/exercise.json"))
    if not books or not exercises:
        raise ContentValidationError("At least one coursebook and exercise are required")

    book_ids: list[str] = []
    module_ids: list[str] = []
    word_ids: list[str] = []
    word_count = 0
    for book_path in books:
        book = read_json(book_path)
        book_id = book.get("id")
        if not book_id or book_path.parent.name != book_id:
            raise ContentValidationError(f"{book_path}: invalid book ID")
        book_ids.append(book_id)
        modules = book.get("modules")
        if not isinstance(modules, list) or not modules:
            raise ContentValidationError(f"{book_id}: modules must not be empty")
        _unique_ids(modules, f"{book_id} modules")
        for module in modules:
            module_id = f"{book_id}:{module['id']}"
            module_ids.append(module_id)
            module_file = book_path.parent / module.get("file", "")
            if not module_file.is_file() or module_file.parent != book_path.parent:
                raise ContentValidationError(f"{module_id}: missing module file")
            words = read_json(module_file)
            if not isinstance(words, list) or not words:
                raise ContentValidationError(f"{module_id}: words must not be empty")
            _unique_ids(words, module_id)
            for word in words:
                word_id = f"{module_id}:{word['id']}"
                word_ids.append(word_id)
                term = word.get("word") or word.get("infinitive")
                if not term or word.get("type") not in {"noun", "verb", "other"}:
                    raise ContentValidationError(f"{word_id}: invalid word card")
                translations = word.get("translation")
                if not isinstance(translations, dict) or not translations:
                    raise ContentValidationError(f"{word_id}: translations missing")
            word_count += len(words)

    _unique_ids([{"id": value} for value in book_ids], "coursebooks")
    _unique_ids([{"id": value} for value in module_ids], "modules")
    _unique_ids([{"id": value} for value in word_ids], "words")

    exercise_ids: list[str] = []
    exercise_word_count = 0
    for exercise_path in exercises:
        exercise = read_json(exercise_path)
        exercise_id = exercise.get("id")
        if not exercise_id or exercise_path.parent.name != exercise_id:
            raise ContentValidationError(f"{exercise_path}: invalid exercise ID")
        exercise_ids.append(exercise_id)
        words_file = exercise.get("wordsFile", "words.json")
        words_path = exercise_path.parent / words_file
        if not words_path.is_file():
            raise ContentValidationError(f"{exercise_id}: missing words file")
        words = read_json(words_path)
        if not isinstance(words, list) or not words:
            raise ContentValidationError(f"{exercise_id}: words must not be empty")
        _unique_ids(words, f"{exercise_id} exercise words")
        exercise_word_count += len(words)

    _unique_ids([{"id": value} for value in exercise_ids], "exercises")
    return {
        "coursebooks": len(books),
        "modules": len(module_ids),
        "words": word_count,
        "exercises": len(exercises),
        "exerciseWords": exercise_word_count,
    }


def validate_published(root: Path) -> None:
    manifest = read_json(root / "manifest.json")
    catalog_ref = manifest.get("catalog", {})
    catalog_path = root / catalog_ref.get("url", "")
    if not catalog_path.is_file():
        raise ContentValidationError("Published catalog is missing")
    if sha256_file(catalog_path) != catalog_ref.get("sha256"):
        raise ContentValidationError("Published catalog checksum mismatch")
    catalog = read_json(catalog_path)
    for source in catalog.get("sources", []):
        descriptor_path = root / source["url"]
        if not descriptor_path.is_file():
            raise ContentValidationError(f"Missing {source['url']}")
        if sha256_file(descriptor_path) != source["sha256"]:
            raise ContentValidationError(f"Checksum mismatch: {source['url']}")
        descriptor = read_json(descriptor_path)
        references = descriptor.get("modules", []) if source["type"] == "coursebook" else [descriptor["words"]]
        for reference in references:
            path = root / reference["url"]
            if not path.is_file() or sha256_file(path) != reference["sha256"]:
                raise ContentValidationError(f"Invalid referenced file: {reference['url']}")

