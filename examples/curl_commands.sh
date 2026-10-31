#!/usr/bin/env bash
# HandAI REST API - cURL Quick Reference Examples

BASE_URL="http://localhost:8000"
API_KEY="sk-handai-development-key"

echo "=== 1. Check API Health ==="
curl -s -X GET "${BASE_URL}/health" \
  -H "X-API-Key: ${API_KEY}" | jq .

echo -e "\n=== 2. Multipart Image Upload OCR ==="
# Replace sample.jpg with your local image file
# curl -s -X POST "${BASE_URL}/v1/ocr/upload" \
#   -H "X-API-Key: ${API_KEY}" \
#   -F "file=@sample.jpg" \
#   -F "mode=handwritten" \
#   -F "enhance_contrast=true" | jq .

echo -e "\n=== 3. Structure Raw Text into Notes / Tasks / Markdown ==="
curl -s -X POST "${BASE_URL}/v1/text/structure" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Meeting Notes 2026-10-31\n- Finish API endpoints\n- Test with pytest\n- Update Dockerfile",
    "target_format": "markdown",
    "extract_action_items": true
  }' | jq .
