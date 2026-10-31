import time
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings
from models.schemas import HealthResponse, ErrorResponse, APIError
from routers import ocr

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# -------------------------------------------------------------
# Cross-Origin Resource Sharing (CORS) - Enables Web / Mobile integration
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-MS"],
)

# -------------------------------------------------------------
# Request Tracing & Performance Timing Middleware
# -------------------------------------------------------------
@app.middleware("http")
async def add_process_time_and_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = str(process_time)
    return response

# -------------------------------------------------------------
# Standardized Error Handlers (Consistent schema across all errors)
# -------------------------------------------------------------
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    detail = exc.detail

    if isinstance(detail, dict):
        code = detail.get("code", "error")
        message = detail.get("message", str(detail))
        details = detail.get("details", None)
    else:
        code = f"http_{exc.status_code}"
        message = str(detail)
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                "details": details,
            }
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected server error occurred.",
                "request_id": request_id,
                "details": {"exception": str(exc)},
            }
        },
    )

# -------------------------------------------------------------
# Core Root & Health Endpoints
# -------------------------------------------------------------
@app.get("/", summary="API Root Info", tags=["General"])
async def root_info():
    """Returns general service metadata, documentation links, and engine status."""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "online",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        },
        "endpoints": {
            "recognize_base64": "POST /v1/ocr/recognize",
            "upload_image": "POST /v1/ocr/upload",
            "batch_pages": "POST /v1/ocr/batch",
            "structure_text": "POST /v1/text/structure",
            "health": "GET /health",
        },
        "authentication": (
            "Open access" if "*" in settings.ALLOWED_API_KEYS
            else "Required (X-API-Key or Bearer token)"
        ),
    }

@app.get("/health", response_model=HealthResponse, summary="Health Check", tags=["General"])
async def health_check():
    """Health check for load balancers, container runners, and uptime monitors."""
    is_gemini_set = bool(settings.GEMINI_API_KEY.strip())
    return HealthResponse(
        status="healthy" if is_gemini_set else "degraded",
        gemini_configured=is_gemini_set,
        version=settings.API_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

# Mount versioned routers
app.include_router(ocr.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
