from __future__ import annotations

import argparse
import json
from pathlib import Path

from dependency_agent.analyser import analyse_paths


def _default_source(pom_path: Path) -> Path:
    return pom_path.parent / "src" / "main" / "java" / "com" / "example" / "App.java"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dependency-agent",
        description="Explain the curated SLF4J Maven dependency failure with evidence.",
    )
    subparsers = parser.add_subparsers(dest="command")
    analyse = subparsers.add_parser("analyse", help="analyse a Maven POM and Java source")
    analyse.add_argument("pom", type=Path, help="path to pom.xml")
    analyse.add_argument("--source", type=Path, help="path to the Java source file")
    analyse.add_argument("--json", action="store_true", help="print structured JSON")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command != "analyse":
        parser.print_help()
        return

    source = args.source or _default_source(args.pom)
    result = analyse_paths(args.pom, source)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print(f"{result.headline} [{result.confidence} confidence]\n")
    print(result.summary)
    for item in result.evidence:
        print(f"\n- {item.source}: {item.value}\n  {item.detail}")
    if result.suggestion:
        print(f"\nSuggested fix: {result.suggestion.summary}\n")
        print(result.suggestion.diff)
    print(f"\nVerification: {result.verification}")
