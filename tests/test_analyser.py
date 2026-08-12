from pathlib import Path

from dependency_agent.analyser import analyse_maven_project, analyse_paths

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "maven" / "demo-app"
SOURCE = DEMO / "src" / "main" / "java" / "com" / "example" / "App.java"


def test_broken_fixture_is_diagnosed_with_minimal_fix() -> None:
    result = analyse_paths(DEMO / "pom_that_do_not_work.xml", SOURCE)

    assert result.status == "conflict"
    assert result.confidence == "high"
    assert result.suggestion is not None
    assert result.suggestion.before == "1.6.6"
    assert result.suggestion.after == "2.0.17"
    assert "-        <version>1.6.6</version>" in result.suggestion.diff
    assert "+        <version>2.0.17</version>" in result.suggestion.diff


def test_working_fixture_is_recognised_as_compatible() -> None:
    result = analyse_paths(DEMO / "pom.xml", SOURCE)

    assert result.status == "compatible"
    assert result.suggestion is None


def test_unrelated_project_is_outside_mvp_scope() -> None:
    result = analyse_maven_project(
        "<project><dependencies /></project>",
        "public class App {}",
    )

    assert result.status == "unsupported"
    assert result.suggestion is None
