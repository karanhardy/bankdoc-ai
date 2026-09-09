from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract


class OCRProcessor:
    """Performs OCR on document images."""

    def __init__(self, tesseract_cmd: str | None = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract_text(self, image_path: Path) -> str:
        """
        Extract text from an image using Tesseract OCR.

        The image is preprocessed before OCR to improve
        recognition quality.
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

        # Convert to grayscale
        image = image.convert("L")

        # Increase contrast
        image = ImageEnhance.Contrast(
            image
        ).enhance(1.5)

        # Reduce small image noise
        image = image.filter(
            ImageFilter.MedianFilter(
                size=3
            )
        )

        # OCR
        text = pytesseract.image_to_string(
            image,
            config="--psm 6",
        )

        return text.strip()