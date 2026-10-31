import base64
import requests

API_BASE_URL = "http://localhost:8000"
API_KEY = "sk-handai-development-key"  # Set to your client API key if configured

headers = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

def test_health():
    """Check API health and model status."""
    res = requests.get(f"{API_BASE_URL}/health", headers=headers)
    print("Health Status:", res.json())

def test_upload(image_path: str):
    """Recognize text by uploading an image file directly (multipart/form-data)."""
    with open(image_path, "rb") as f:
        files = {"file": (image_path, f, "image/jpeg")}
        data = {
            "mode": "handwritten",
            "enhance_contrast": "true",
            "auto_correct_common_errors": "true"
        }
        res = requests.post(f"{API_BASE_URL}/v1/ocr/upload", headers=headers, files=files, data=data)
        
        if res.status_code == 200:
            result = res.json()
            print("Extracted Text:\n", result["data"]["text"])
            print("Confidence:", result["data"]["confidence"])
        else:
            print("Error:", res.status_code, res.json())

def test_recognize_base64(image_path: str):
    """Recognize text via JSON payload containing a Base64 encoded image."""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
        
    payload = {
        "image_base64": b64,
        "mode": "handwritten",
        "enhance_contrast": True,
        "auto_correct_common_errors": True
    }
    
    res = requests.post(f"{API_BASE_URL}/v1/ocr/recognize", headers=headers, json=payload)
    print("Base64 Response:", res.json())

if __name__ == "__main__":
    test_health()
    # test_upload("sample_note.jpg")
