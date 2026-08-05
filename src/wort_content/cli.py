from __future__ import annotations

import argparse
from pathlib import Path

from .builder import build_content
from .validator import validate_published, validate_source


def main() -> None:
    parser = argparse.ArgumentParser(prog="wort-content")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--source", type=Path, default=Path("data/source"))
    build.add_argument("--output", type=Path, default=Path("data/published"))
    validate = subparsers.add_parser("validate")
    validate.add_argument("--source", type=Path, default=Path("data/source"))
    validate.add_argument("--published", type=Path, default=Path("data/published"))
    args = parser.parse_args()
    if args.command == "build":
        result = build_content(args.source, args.output)
        print(f"Published {result['words']} learning words as {result['version']}")
    else:
        counts = validate_source(args.source)
        validate_published(args.published)
        print(f"Validated content: {counts}")


if __name__ == "__main__":
    main()
