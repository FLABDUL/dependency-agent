"""Build a self-contained Cloudflare Worker for the public portfolio demo."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from dependency_agent.analyser import analyse_paths

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DEMO = ROOT / "maven" / "demo-app"
OUTPUT = ROOT / "dist" / "server" / "index.js"


def javascript_constant(name: str, value: object) -> str:
    return f"const {name} = {json.dumps(value, separators=(',', ':'))};\n"


def main() -> None:
    pom_path = DEMO / "pom_that_do_not_work.xml"
    source_path = DEMO / "src" / "main" / "java" / "com" / "example" / "App.java"
    payload = {
        "result": analyse_paths(pom_path, source_path).to_dict(),
        "input": {
            "pom": pom_path.read_text(encoding="utf-8"),
            "source": source_path.read_text(encoding="utf-8"),
        },
    }

    worker = "".join(
        (
            javascript_constant("HTML", (STATIC / "index.html").read_text(encoding="utf-8")),
            javascript_constant("CSS", (STATIC / "styles.css").read_text(encoding="utf-8")),
            javascript_constant("APP_JS", (STATIC / "app.js").read_text(encoding="utf-8")),
            javascript_constant("DEMO", payload),
            javascript_constant(
                "OG_BASE64", base64.b64encode((STATIC / "og.png").read_bytes()).decode("ascii")
            ),
            """
const textHeaders = (contentType) => ({
  "content-type": contentType,
  "cache-control": "public, max-age=300",
  "x-content-type-options": "nosniff",
  "referrer-policy": "strict-origin-when-cross-origin",
});

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/") {
      return new Response(HTML, { headers: textHeaders("text/html; charset=utf-8") });
    }
    if (url.pathname === "/static/styles.css") {
      return new Response(CSS, { headers: textHeaders("text/css; charset=utf-8") });
    }
    if (url.pathname === "/static/app.js") {
      return new Response(APP_JS, { headers: textHeaders("text/javascript; charset=utf-8") });
    }
    if (url.pathname === "/static/og.png") {
      const bytes = Uint8Array.from(atob(OG_BASE64), (character) => character.charCodeAt(0));
      return new Response(bytes, { headers: textHeaders("image/png") });
    }
    if (url.pathname === "/api/demo") {
      return Response.json(DEMO, { headers: { "cache-control": "public, max-age=300" } });
    }
    if (url.pathname === "/api/health") {
      return Response.json({ status: "ok" });
    }
    return new Response("Not found", { status: 404 });
  },
};
""",
        )
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(worker, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
