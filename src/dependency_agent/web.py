from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from dependency_agent.analyser import analyse_paths

ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT / "static"
DEMO_DIR = ROOT / "maven" / "demo-app"

app = FastAPI(
    title="Dependency Agent",
    description="A focused demonstration of evidence-led Maven dependency diagnosis.",
    docs_url=None,
    redoc_url=None,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/api/demo")
def demo() -> dict[str, object]:
    pom_path = DEMO_DIR / "pom_that_do_not_work.xml"
    source_path = DEMO_DIR / "src" / "main" / "java" / "com" / "example" / "App.java"
    result = analyse_paths(pom_path, source_path)
    return {
        "result": result.to_dict(),
        "input": {
            "pom": pom_path.read_text(encoding="utf-8"),
            "source": source_path.read_text(encoding="utf-8"),
        },
    }


@app.get("/", response_class=FileResponse)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
