from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# -------------------------------------------------------------
# Standard Error Model (Per API Platform Engineer Spec)
# -------------------------------------------------------------
class APIError(BaseModel):
    code: str = Field(..., description="Stable, machine-readable error code", json_schema_extra={"example": "invalid_image"})
    message: str = Field(..., description="Human-readable explanation", json_schema_extra={"example": "The provided image could not be decoded."})
    request_id: Optional[str] = Field(None, description="Unique trace identifier for diagnostics")
    details: Optional[Dict[str, Any]] = Field(None, description="Contextual debugging details")

class ErrorResponse(BaseModel):
    error: APIError

# -------------------------------------------------------------
# Structured Block Schema
# -------------------------------------------------------------
class StructuredBlock(BaseModel):
    type: str = Field(..., description="Block type: heading, list-item, paragraph, code", json_schema_extra={"example": "heading"})
    content: str = Field(..., description="Extracted block text", json_schema_extra={"example": "# Project Architecture"})
    level: Optional[int] = Field(None, description="Heading level (1-6) if applicable", json_schema_extra={"example": 1})

# -------------------------------------------------------------
# OCR Request & Response Schemas
# -------------------------------------------------------------
class OCRRecognizeRequest(BaseModel):
    image_base64: str = Field(
        ...,
        description="Base64-encoded image string (with or without data:image/jpeg;base64, prefix)",
        json_schema_extra={"example": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ..."}
    )
    format: str = Field(
        default="markdown",
        description="Desired output format: 'markdown', 'plain_text', or 'json_blocks'",
        json_schema_extra={"example": "markdown"}
    )
    enhance_contrast: bool = Field(
        default=True,
        description="Whether to run automatic contrast stretching and grayscale normalization before recognition"
    )
    language_hint: Optional[str] = Field(
        default="auto",
        description="Optional language hint for OCR engine (e.g. 'en', 'es', 'fr', 'auto')"
    )

class OCRRecognizeResponse(BaseModel):
    success: bool = Field(default=True, json_schema_extra={"example": True})
    text: str = Field(..., description="Extracted text in formatted Markdown", json_schema_extra={"example": "# Meeting Notes\n- Review roadmap\n- Deploy API"})
    confidence: float = Field(..., description="Confidence score estimated by model (0-100)", json_schema_extra={"example": 97.5})
    model_used: str = Field(..., description="Underlying Gemini Vision model used for extraction", json_schema_extra={"example": "gemini-2.5-flash"})
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds", json_schema_extra={"example": 1420.5})
    blocks: Optional[List[StructuredBlock]] = Field(None, description="Parsed structural blocks")

class OCRBatchRequest(BaseModel):
    images: List[str] = Field(
        ...,
        description="List of base64-encoded image strings representing document pages",
        min_length=1,
        max_length=50
    )
    format: str = Field(default="markdown", description="Desired output format")
    enhance_contrast: bool = Field(default=True)

class OCRBatchResponse(BaseModel):
    success: bool = Field(default=True)
    text: str = Field(..., description="Unified multi-page Markdown document")
    pages_processed: int = Field(..., json_schema_extra={"example": 3})
    model_used: str = Field(..., json_schema_extra={"example": "gemini-2.5-flash"})
    processing_time_ms: float = Field(..., json_schema_extra={"example": 3240.0})

# -------------------------------------------------------------
# Text Structuring Utility Schemas
# -------------------------------------------------------------
class StructureTextRequest(BaseModel):
    raw_text: str = Field(
        ...,
        description="Raw or noisy OCR text to be formatted and corrected",
        json_schema_extra={"example": "1. PROJECT GOALS\nTh|s is a 5pec1al system\n- item A"}
    )

class StructureTextResponse(BaseModel):
    markdown: str = Field(..., description="Cleaned and formatted Markdown")
    blocks: List[StructuredBlock] = Field(..., description="Extracted structural blocks")

# -------------------------------------------------------------
# System & Health Schemas
# -------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = Field(default="healthy", json_schema_extra={"example": "healthy"})
    gemini_configured: bool = Field(..., description="True if GEMINI_API_KEY is configured on the server")
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    timestamp: str = Field(..., json_schema_extra={"example": "2026-10-31T18:00:00Z"})
