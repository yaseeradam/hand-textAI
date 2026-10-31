# HandAI REST API Backend 🚀

A production-grade, fast, cross-stack REST API that wraps the HandAI Gemini Vision OCR and document structuring engine.

Built with **FastAPI**, **Python 3.13**, and **Pydantic V2**, following strict API platform standards (`agency-api-platform-engineer`).

---

## 🌟 Why This API?

1. **Security & Key Protection**: Your private Google Gemini API key stays safe on your server. Clients and apps call your API using client tokens (`X-API-Key`) that you control and can revoke anytime.
2. **Universal Stack Integration**: Can be integrated into **Flutter, React, Vue, Next.js, Node.js, Python, Swift, Kotlin, Go**, or any stack that can make an HTTP request.
3. **Multi-Format Support**: Supports Base64 JSON payloads, direct multipart file uploads, and multi-page batch OCR.
4. **Intelligent Text Post-Processing**: Includes automatic OCR misread correction, contrast/orientation normalization, and semantic block structuring (Markdown, Todo list, outline).

---

## ⚡ Quick Start

### 1. Setup Environment
```bash
# Clone or navigate to the API directory
cd hand_ai_api

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env    # Windows
cp .env.example .env      # Linux / macOS
```
Edit `.env` with your Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
ALLOWED_API_KEYS=sk-handai-client-1,sk-handai-client-2
DEFAULT_MODEL=gemini-2.5-flash
```
*(If `ALLOWED_API_KEYS` is left empty, the API accepts all requests in open/development mode).*

### 3. Run the Server
```bash
python -m uvicorn main:app --reload --port 8000
```
Your API is now live at:
- **Interactive Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON Specification**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🐳 Docker Deployment

### Run with Docker:
```bash
docker build -t hand-ai-api .
docker run -p 8000:8000 --env-file .env hand-ai-api
```

### Or with Docker Compose:
```bash
docker compose up -d
```

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health, uptime, and Gemini API readiness. |
| `POST` | `/v1/ocr/recognize` | Transcribe handwriting from Base64 JSON payload. |
| `POST` | `/v1/ocr/upload` | Transcribe handwriting via direct image file upload (`multipart/form-data`). |
| `POST` | `/v1/ocr/batch` | Batch process multiple pages or images concurrently. |
| `POST` | `/v1/text/structure` | Convert raw transcribed text into structured blocks, Markdown, or action items. |

---

## 🔑 Authentication

Send your client API key in either:
- **Header**: `X-API-Key: your_key`
- **Bearer Token**: `Authorization: Bearer your_key`
- **Query Parameter**: `?api_key=your_key`

---

## 💻 Client Integration Examples

Working code examples are provided in the [`examples/`](file:///c:/Users/AI%20ACADEMY/Documents/antigravity/vibrant-galileo/hand_ai_api/examples) directory:
- [Python Example (`examples/python_client.py`)](file:///c:/Users/AI%20ACADEMY/Documents/antigravity/vibrant-galileo/hand_ai_api/examples/python_client.py)
- [JavaScript / Node.js Example (`examples/javascript_client.js`)](file:///c:/Users/AI%20ACADEMY/Documents/antigravity/vibrant-galileo/hand_ai_api/examples/javascript_client.js)
- [Dart / Flutter Example (`examples/flutter_client.dart`)](file:///c:/Users/AI%20ACADEMY/Documents/antigravity/vibrant-galileo/hand_ai_api/examples/flutter_client.dart)
- [cURL Command Reference (`examples/curl_commands.sh`)](file:///c:/Users/AI%20ACADEMY/Documents/antigravity/vibrant-galileo/hand_ai_api/examples/curl_commands.sh)

---

## 🧪 Testing

Run automated tests with `pytest`:
```bash
python -m pytest tests/test_api.py -v
```
All 6 tests validate schema validation, authentication enforcement, image preprocessing, and error formats.
