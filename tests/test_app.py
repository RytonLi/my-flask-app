import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_hello(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json["message"] == "Hello, CI/CD!"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_get_time(client):
    response = client.get("/api/time")
    assert response.status_code == 200
    assert "current_time" in response.json


def test_greet(client):
    response = client.get("/greet/John")
    assert response.status_code == 200
    assert response.json["message"] == "Hello, John!"


def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json["version"] == "1.0.0"
