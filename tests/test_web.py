from fastapi.testclient import TestClient

from dependency_agent.web import app

client = TestClient(app)


def test_demo_endpoint_returns_real_analysis() -> None:
    response = client.get("/api/demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["status"] == "conflict"
    assert payload["result"]["suggestion"]["after"] == "2.0.17"


def test_health_endpoint() -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_home_page_serves_the_demo() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "A broken build" in response.text


def test_favicon_request_is_quiet() -> None:
    assert client.get("/favicon.ico").status_code == 204
