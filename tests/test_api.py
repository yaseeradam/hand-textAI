import base64
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from main import app
from config import settings
from services.text_service import TextService
from services.image_service import ImageService

client = TestClient(app)

def create_test_base64_image(width=100, height=50, color=(255, 255, 255)) -> str:
    """Helper to generate a small synthetic JPEG in base64."""
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "documentation" in data
    assert "endpoints" in data
    assert "/v1/ocr/recognize" in data["endpoints"]["recognize_base64"]

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "gemini_configured" in data
    assert "version" in data
    assert "timestamp" in data

def test_text_structure_endpoint():
    raw_sample = (
        "# PROJECT OVERVIEW\n"
        "Th|s is a 5pec1al note with 0CR artifacts.\n\n"
        "- Task 1: Complete setup\n"
        "- Task 2: Verify API\n"
    )
    response = client.post("/v1/text/structure", json={"raw_text": raw_sample})
    assert response.status_code == 200
    data = response.json()
    assert "markdown" in data
    assert "blocks" in data
    assert "ThIs is a special note" in data["markdown"]
    assert any(b["type"] == "heading" for b in data["blocks"])
    assert any(b["type"] == "list-item" for b in data["blocks"])

def test_image_preprocessing():
    test_b64 = create_test_base64_image(width=3000, height=2000)
    raw_bytes = ImageService.decode_base64_to_bytes(test_b64)
    processed_bytes, processed_b64 = ImageService.preprocess_image(
        raw_bytes,
        enhance_contrast=True,
        max_dimension=1024,
    )
    assert len(processed_bytes) > 0
    assert len(processed_b64) > 0

    # Verify downscaled within max_dimension
    processed_img = Image.open(io.BytesIO(processed_bytes))
    assert processed_img.width <= 1024
    assert processed_img.height <= 1024

def test_recognize_invalid_base64():
    response = client.post("/v1/ocr/recognize", json={"image_base64": "not_valid_base64!!"})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] in ["invalid_base64", "image_preprocessing_failed"]
    assert "request_id" in data["error"]

def test_authentication_enforcement(monkeypatch):
    # Temporarily enforce API keys
    monkeypatch.setattr(settings, "ALLOWED_API_KEYS", ["secret_key_123"])

    # 1. Unauthenticated request -> 401
    response = client.post(
        "/v1/text/structure",
        json={"raw_text": "hello"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"

    # 2. Authenticated with X-API-Key -> 200
    auth_response = client.post(
        "/v1/text/structure",
        json={"raw_text": "hello"},
        headers={"X-API-Key": "secret_key_123"},
    )
    assert auth_response.status_code == 200

    # 3. Authenticated with Bearer token -> 200
    bearer_response = client.post(
        "/v1/text/structure",
        json={"raw_text": "hello"},
        headers={"Authorization": "Bearer secret_key_123"},
    )
    assert bearer_response.status_code == 200
