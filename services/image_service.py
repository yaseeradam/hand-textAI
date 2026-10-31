import base64
import io
from PIL import Image, ImageOps, ImageEnhance

class ImageService:
    @staticmethod
    def decode_base64_to_bytes(base64_str: str) -> bytes:
        """Strips data URI prefix if present and decodes base64 string."""
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        return base64.b64decode(base64_str.strip())

    @staticmethod
    def preprocess_image(
        image_bytes: bytes,
        enhance_contrast: bool = True,
        max_dimension: int = 2048,
        jpeg_quality: int = 88,
    ) -> tuple[bytes, str]:
        """
        Preprocesses image for optimal OCR:
        - Auto-orients via EXIF
        - Scales down if excessively large
        - Normalizes contrast and sharpness for ink readability
        Returns (jpeg_bytes, base64_string).
        """
        image = Image.open(io.BytesIO(image_bytes))

        # 1. Correct orientation using EXIF tags
        image = ImageOps.exif_transpose(image)

        # 2. Convert to RGB (handles RGBA or Paletted images)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # 3. Downscale if dimensions exceed max_dimension
        width, height = image.size
        if width > max_dimension or height > max_dimension:
            scaling = min(max_dimension / width, max_dimension / height)
            new_size = (int(width * scaling), int(height * scaling))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # 4. Optional contrast enhancement for faded handwriting
        if enhance_contrast:
            # Subtle contrast boost to separate ink from paper grain
            contrast = ImageEnhance.Contrast(image)
            image = contrast.enhance(1.25)
            # Subtle sharpness boost for edge definition
            sharpness = ImageEnhance.Sharpness(image)
            image = sharpness.enhance(1.15)

        # 5. Export to compressed JPEG buffer
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
        processed_bytes = output_buffer.getvalue()
        processed_b64 = base64.b64encode(processed_bytes).decode("utf-8")

        return processed_bytes, processed_b64
