/**
 * HandAI API - Node.js / JavaScript Browser Client Example
 * Compatible with Node.js 18+ and all modern browsers.
 */

const API_BASE_URL = "http://localhost:8000";
const API_KEY = "sk-handai-development-key";

// 1. Health check
async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, {
    headers: {
      "X-API-Key": API_KEY,
    },
  });
  const data = await response.json();
  console.log("API Health:", data);
}

// 2. Recognize handwriting with Base64 JSON
async function recognizeBase64(base64Image) {
  const response = await fetch(`${API_BASE_URL}/v1/ocr/recognize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
    },
    body: JSON.stringify({
      image_base64: base64Image,
      mode: "handwritten",
      enhance_contrast: true,
      auto_correct_common_errors: true,
    }),
  });

  const result = await response.json();
  if (result.success) {
    console.log("Transcribed text:", result.data.text);
    console.log("Word count:", result.data.word_count);
  } else {
    console.error("OCR Failed:", result.error);
  }
}

// 3. Recognize using FormData (File / Blob upload)
async function uploadImage(fileBlob, filename = "note.jpg") {
  const formData = new FormData();
  formData.append("file", fileBlob, filename);
  formData.append("mode", "handwritten");
  formData.append("enhance_contrast", "true");

  const response = await fetch(`${API_BASE_URL}/v1/ocr/upload`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
    },
    body: formData,
  });

  const result = await response.json();
  console.log("Upload result:", result);
}

// Export for Node / ES module usage
if (typeof module !== "undefined" && module.exports) {
  module.exports = { checkHealth, recognizeBase64, uploadImage };
}
