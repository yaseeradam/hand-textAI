import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from middleware.auth import verify_client_key
from models.schemas import (
    OCRRecognizeRequest,
    OCRRecognizeResponse,
    OCRBatchRequest,
    OCRBatchResponse,
    StructureTextRequest,
    StructureTextResponse,
    ErrorResponse,
)
from services.image_service import ImageService
from services.text_service import TextService
from services.gemini_service import GeminiService

router = APIRouter(prefix="/v1", tags=["OCR & Document Recognition"])

@router.post(
    "/ocr/recognize",
    response_model=OCRRecognizeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid image or base64 format"},
        401: {"model": ErrorResponse, "description": "Unauthorized access"},
        500: {"model": ErrorResponse, "description": "AI extraction error"},
    },
    summary="Recognize handwriting from a Base64 image",
    description="Accepts a Base64 encoded image, applies preprocessing, extracts text using Gemini Vision, and returns structured Markdown.",
)
async def recognize_base64_image(
    payload: OCRRecognizeRequest,
    client: str = Depends(verify_client_key),
):
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())

    try:
        raw_bytes = ImageService.decode_base64_to_bytes(payload.image_base64)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_base64",
                "message": f"Could not decode base64 image string: {str(e)}",
                "request_id": request_id,
            },
        )

    try:
        _, processed_b64 = ImageService.preprocess_image(
            raw_bytes,
            enhance_contrast=payload.enhance_contrast,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "image_preprocessing_failed",
                "message": f"Failed to preprocess image: {str(e)}",
                "request_id": request_id,
            },
        )

    try:
        extracted_text, confidence, model = await GeminiService.extract_text_from_image(
            processed_b64,
            language_hint=payload.language_hint,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_configuration_error",
                "message": str(e),
                "request_id": request_id,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "vision_ai_error",
                "message": f"Google Gemini Vision API failed: {str(e)}",
                "request_id": request_id,
            },
        )

    cleaned_text = TextService.clean_ocr_text(extracted_text)
    blocks = TextService.structure_text(cleaned_text)

    # Format result depending on request
    final_text = cleaned_text
    if payload.format == "markdown":
        final_text = TextService.blocks_to_markdown(blocks)
    elif payload.format == "plain_text":
        final_text = "\n".join([b.content.lstrip("#-•* ") for b in blocks])

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return OCRRecognizeResponse(
        success=True,
        text=final_text,
        confidence=confidence,
        model_used=model,
        processing_time_ms=duration_ms,
        blocks=blocks if payload.format == "json_blocks" else None,
    )

@router.post(
    "/ocr/upload",
    response_model=OCRRecognizeResponse,
    summary="Upload image file directly for OCR",
    description="Accepts multipart/form-data image upload (JPEG, PNG, WEBP), processes and extracts structured notes.",
)
async def upload_image_file(
    file: UploadFile = File(..., description="Image file to digitize"),
    enhance_contrast: bool = Form(default=True, description="Enhance contrast for faint handwriting"),
    language_hint: Optional[str] = Form(default="auto", description="Language hint"),
    client: str = Depends(verify_client_key),
):
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "unsupported_media_type",
                "message": f"Uploaded file must be an image. Received: {file.content_type}",
                "request_id": request_id,
            },
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "empty_file",
                "message": "The uploaded file is empty.",
                "request_id": request_id,
            },
        )

    try:
        _, processed_b64 = ImageService.preprocess_image(
            file_bytes,
            enhance_contrast=enhance_contrast,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "image_decode_failed",
                "message": f"Failed to read image format: {str(e)}",
                "request_id": request_id,
            },
        )

    try:
        extracted_text, confidence, model = await GeminiService.extract_text_from_image(
            processed_b64,
            language_hint=language_hint,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "vision_ai_error",
                "message": str(e),
                "request_id": request_id,
            },
        )

    cleaned = TextService.clean_ocr_text(extracted_text)
    blocks = TextService.structure_text(cleaned)
    markdown = TextService.blocks_to_markdown(blocks)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return OCRRecognizeResponse(
        success=True,
        text=markdown,
        confidence=confidence,
        model_used=model,
        processing_time_ms=duration_ms,
        blocks=blocks,
    )

@router.post(
    "/ocr/batch",
    response_model=OCRBatchResponse,
    summary="Batch multi-page handwriting OCR",
    description="Processes an array of handwritten pages and merges them into a single coherent document.",
)
async def process_batch_pages(
    payload: OCRBatchRequest,
    client: str = Depends(verify_client_key),
):
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())

    extracted_pages = []
    used_model = "gemini-2.5-flash"

    for idx, page_b64 in enumerate(payload.images, start=1):
        try:
            raw_bytes = ImageService.decode_base64_to_bytes(page_b64)
            _, processed_b64 = ImageService.preprocess_image(
                raw_bytes,
                enhance_contrast=payload.enhance_contrast,
            )
            page_text, _, model = await GeminiService.extract_text_from_image(processed_b64)
            used_model = model
            cleaned = TextService.clean_ocr_text(page_text)
            extracted_pages.append(f"## Page {idx}\n\n{cleaned}")
        except Exception as e:
            extracted_pages.append(f"## Page {idx}\n\n*[OCR Extraction Failed: {str(e)}]*")

    merged_markdown = "\n\n---\n\n".join(extracted_pages)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return OCRBatchResponse(
        success=True,
        text=merged_markdown,
        pages_processed=len(payload.images),
        model_used=used_model,
        processing_time_ms=duration_ms,
    )

@router.post(
    "/text/structure",
    response_model=StructureTextResponse,
    summary="Clean and structure raw OCR text",
    description="Post-processes raw text: eliminates OCR character mistakes, normalizes headings, and generates blocks.",
)
async def structure_raw_text(
    payload: StructureTextRequest,
    client: str = Depends(verify_client_key),
):
    cleaned = TextService.clean_ocr_text(payload.raw_text)
    blocks = TextService.structure_text(cleaned)
    markdown = TextService.blocks_to_markdown(blocks)

    return StructureTextResponse(
        markdown=markdown,
        blocks=blocks,
    )
