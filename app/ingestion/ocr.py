from pathlib import Path

from PIL import Image
import pytesseract


class OCRProcessor:
    """Performs OCR on document images."""

    def __init__(self, tesseract_cmd: str | None = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract_text(self, image_path: Path) -> str:
        """
        Extract text from an image using Tesseract OCR.

        Args:
            image_path: Path to the image.

        Returns:
            Extracted text.
        """

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        if not image_path.is_file():
            raise ValueError(
                f"Expected a file, got: {image_path}"
            )

        image = Image.open(image_path)

        text = pytesseract.image_to_string(image)

        return text.strip()