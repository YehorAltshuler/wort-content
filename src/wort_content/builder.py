from __future__ import annotations

import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .util import read_json, sha256_file, write_json
from .validator import validate_published, validate_source


def _publish_atomically(staged: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    backup = output.with_name(f"{output.name}.previous")
    if backup.exists():
        shutil.rmtree(backup)
    if output.exists():
        output.rename(backup)
    try:
        staged.rename(output)
    except Exception:
        if output.exists():
            shutil.rmtree(output)
        if backup.exists():
            backup.rename(output)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup)


def build_content(source: Path, output: Path) -> dict:
    counts = validate_source(source)
    now = datetime.now(UTC)
    version = now.strftime("%Y-%m-%d.%H%M%S")
    with tempfile.TemporaryDirectory(prefix="wort-content-", dir=output.parent) as temporary:
        staged = Path(temporary) / output.name
        staged.mkdir(parents=True)
        sources: list[dict] = []

        for book_path in sorted((source / "coursebooks").glob("*/book.json")):
            book = read_json(book_path)
            target_dir = staged / "coursebooks" / book["id"]
            modules = []
            for module in book["modules"]:
                source_module = book_path.parent / module["file"]
                target_module = target_dir / module["file"]
                write_json(target_module, read_json(source_module))
                modules.append({
                    "id": module["id"],
                    "title": module["title"],
                    "url": str(target_module.relative_to(staged)),
                    "sha256": sha256_file(target_module),
                    "count": len(read_json(target_module)),
                })
            descriptor = {
                "schemaVersion": 1,
                "contentVersion": version,
                "id": book["id"],
                "title": book["title"],
                "level": book["level"],
                "modules": modules,
            }
            descriptor_path = target_dir / "book.json"
            write_json(descriptor_path, descriptor)
            sources.append({
                "id": book["id"],
                "type": "coursebook",
                "url": str(descriptor_path.relative_to(staged)),
                "sha256": sha256_file(descriptor_path),
            })

        for exercise_path in sorted((source / "exercises").glob("*/exercise.json")):
            exercise = read_json(exercise_path)
            target_dir = staged / "exercises" / exercise["id"]
            words_path = target_dir / "words.json"
            words = read_json(exercise_path.parent / exercise.get("wordsFile", "words.json"))
            write_json(words_path, words)
            descriptor = {
                "schemaVersion": 1,
                "contentVersion": version,
                **{key: value for key, value in exercise.items() if key != "wordsFile"},
                "words": {
                    "url": str(words_path.relative_to(staged)),
                    "sha256": sha256_file(words_path),
                    "count": len(words),
                },
            }
            descriptor_path = target_dir / "exercise.json"
            write_json(descriptor_path, descriptor)
            sources.append({
                "id": exercise["id"],
                "type": "exercise",
                "url": str(descriptor_path.relative_to(staged)),
                "sha256": sha256_file(descriptor_path),
            })

        catalog_path = staged / "catalog.json"
        write_json(catalog_path, {
            "schemaVersion": 1,
            "contentVersion": version,
            "generatedAt": now.isoformat().replace("+00:00", "Z"),
            "sources": sources,
        })
        write_json(staged / "manifest.json", {
            "schemaVersion": 1,
            "datasetVersion": version,
            "generatedAt": now.isoformat().replace("+00:00", "Z"),
            "minimumAppVersion": "1.0.0",
            "catalog": {
                "url": "catalog.json",
                "sha256": sha256_file(catalog_path),
                "sourceCount": len(sources),
            },
            "counts": counts,
        })
        validate_published(staged)
        _publish_atomically(staged, output)
    return {"version": version, **counts}

