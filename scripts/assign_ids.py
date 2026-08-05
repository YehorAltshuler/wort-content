#!/usr/bin/env python3
"""Assign explicit stable IDs to source records that do not have one yet."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().strip()
    return re.sub(r"[^a-z0-9äöüß]+", "-", value).strip("-")


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unique_id(base: str, seen: Counter[str]) -> str:
    seen[base] += 1
    return base if seen[base] == 1 else f"{base}-{seen[base]}"


def assign_course_ids() -> None:
    for book_path in sorted((ROOT / "data/source/coursebooks").glob("*/book.json")):
        book = json.loads(book_path.read_text(encoding="utf-8"))
        for module in book["modules"]:
            if not isinstance(module.get("id"), str):
                module["id"] = Path(module["file"]).stem
            module_path = book_path.parent / module["file"]
            words = json.loads(module_path.read_text(encoding="utf-8"))
            seen: Counter[str] = Counter()
            for word in words:
                if word.get("id"):
                    seen[word["id"]] += 1
                    continue
                term = word.get("word") or word.get("infinitive")
                base = slugify(word.get("dictionaryId") or term)
                word["id"] = unique_id(base, seen)
            write(module_path, words)
        write(book_path, book)


def assign_exercise_ids() -> None:
    for exercise_path in sorted((ROOT / "data/source/exercises").glob("*/exercise.json")):
        exercise = json.loads(exercise_path.read_text(encoding="utf-8"))
        exercise.setdefault("wordsFile", "words.json")
        words_path = exercise_path.parent / exercise["wordsFile"]
        words = json.loads(words_path.read_text(encoding="utf-8"))
        seen: Counter[str] = Counter()
        for word in words:
            if word.get("id"):
                seen[word["id"]] += 1
                continue
            base = slugify(f"{word['verb']}-{word['preposition']}-{word['case']}")
            word["id"] = unique_id(base, seen)
        write(words_path, words)
        write(exercise_path, exercise)


if __name__ == "__main__":
    assign_course_ids()
    assign_exercise_ids()
