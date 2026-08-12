from __future__ import annotations

import difflib
import re
from pathlib import Path
from xml.etree import ElementTree

from dependency_agent.models import AnalysisResult, Evidence, SuggestedChange

SLF4J_GROUP = "org.slf4j"
SLF4J_ARTIFACT = "slf4j-api"
COMPATIBLE_SLF4J_VERSION = "2.0.17"
LOGGING_EVENT_BUILDER = "org.slf4j.spi.LoggingEventBuilder"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _dependency_version(pom_text: str, group_id: str, artifact_id: str) -> str | None:
    try:
        root = ElementTree.fromstring(pom_text)
    except ElementTree.ParseError:
        return None

    for element in root.iter():
        if _local_name(element.tag) != "dependency":
            continue
        values = {
            _local_name(child.tag): (child.text or "").strip()
            for child in element
        }
        if values.get("groupId") == group_id and values.get("artifactId") == artifact_id:
            return values.get("version")
    return None


def _major_version(version: str) -> int | None:
    match = re.match(r"\s*(\d+)", version)
    return int(match.group(1)) if match else None


def _replace_dependency_version(pom_text: str, current: str, replacement: str) -> str:
    dependency_pattern = re.compile(
        r"(<dependency>\s*"
        r"<groupId>org\.slf4j</groupId>\s*"
        r"<artifactId>slf4j-api</artifactId>\s*"
        r"<version>)"
        + re.escape(current)
        + r"(</version>)",
        re.MULTILINE,
    )
    return dependency_pattern.sub(rf"\g<1>{replacement}\g<2>", pom_text, count=1)


def _unified_diff(before: str, after: str, filename: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )


def analyse_maven_project(
    pom_text: str,
    source_text: str,
    *,
    filename: str = "pom.xml",
) -> AnalysisResult:
    """Analyse the MVP's concrete SLF4J API/version compatibility scenario.

    The analyser is deliberately deterministic: it links a source-level API
    requirement to the declared Maven version, then produces the smallest POM
    edit that restores compatibility.
    """

    version = _dependency_version(pom_text, SLF4J_GROUP, SLF4J_ARTIFACT)
    uses_builder = LOGGING_EVENT_BUILDER in source_text or "LoggingEventBuilder" in source_text

    if version is None or not uses_builder:
        missing = []
        if version is None:
            missing.append("a direct org.slf4j:slf4j-api dependency")
        if not uses_builder:
            missing.append("a LoggingEventBuilder usage")
        return AnalysisResult(
            status="unsupported",
            headline="No supported SLF4J mismatch found",
            summary="This MVP currently diagnoses one curated Maven failure and could not find "
            + " and ".join(missing)
            + ".",
            confidence="high",
            evidence=(),
            suggestion=None,
            verification="No change proposed.",
        )

    evidence = (
        Evidence(
            source="Java source",
            detail="The project imports and uses the fluent logging API introduced in SLF4J 2.x.",
            value="org.slf4j.spi.LoggingEventBuilder",
        ),
        Evidence(
            source=filename,
            detail="Maven is instructed to compile against this direct dependency version.",
            value=f"org.slf4j:slf4j-api:{version}",
        ),
    )

    if (_major_version(version) or 0) >= 2:
        return AnalysisResult(
            status="compatible",
            headline="SLF4J API and dependency are compatible",
            summary=f"LoggingEventBuilder requires SLF4J 2.x and the POM declares {version}.",
            confidence="high",
            evidence=evidence,
            suggestion=None,
            verification="The supplied version satisfies the detected API requirement.",
        )

    updated_pom = _replace_dependency_version(
        pom_text, version, COMPATIBLE_SLF4J_VERSION
    )
    suggestion = SuggestedChange(
        file=filename,
        summary=f"Upgrade org.slf4j:slf4j-api from {version} to {COMPATIBLE_SLF4J_VERSION}.",
        before=version,
        after=COMPATIBLE_SLF4J_VERSION,
        diff=_unified_diff(pom_text, updated_pom, filename),
    )

    return AnalysisResult(
        status="conflict",
        headline="SLF4J API version mismatch",
        summary=(
            "The Java source uses LoggingEventBuilder, which is part of SLF4J 2.x, "
            f"but Maven compiles the project with slf4j-api {version}. The older JAR "
            "does not contain that type, so compilation fails before the application can run."
        ),
        confidence="high",
        evidence=evidence,
        suggestion=suggestion,
        verification=(
            f"The repository's working fixture uses slf4j-api {COMPATIBLE_SLF4J_VERSION}; "
            "the same source compiles when that dependency is selected."
        ),
    )


def analyse_paths(pom_path: Path, source_path: Path) -> AnalysisResult:
    return analyse_maven_project(
        pom_path.read_text(encoding="utf-8"),
        source_path.read_text(encoding="utf-8"),
        filename=pom_path.name,
    )
