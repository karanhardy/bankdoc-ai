from pathlib import Path

from app.ingestion.pdf_processor import PDFProcessor
from app.ingestion.ocr import OCRProcessor
from app.ingestion.document_normalizer import DocumentNormalizer


class DocumentExtractor:
    """
    Extracts text from a PDF.

    Strategy:
    1. Try native PDF text extraction.
    2. If insufficient text is found, fall back to OCR.
    """

    MIN_TEXT_LENGTH = 50

    def __init__(self, pdf_path: Path):
        self.pdf_path = Path(pdf_path)

        self.pdf_processor = PDFProcessor(
            self.pdf_path
        )
        self.ocr_processor = OCRProcessor()
        self.normalizer = DocumentNormalizer()

    def extract(self) -> list[dict]:
        """
        Extract text from every page.

        Returns:
            List of page-level dictionaries containing:
            - page_number
            - text
            - extraction_method
        """

        pages = self.pdf_processor.extract_text()

        if self._has_sufficient_text(pages):
            print(
                "       Extraction method: Native PDF text"
            )

            return [
                {
                    **page,
                    "extraction_method": "native",
                }
                for page in pages
            ]

        print(
            "       Native text insufficient."
        )

        print(
            "       Falling back to OCR..."
        )

        return self._extract_using_ocr()

    def _has_sufficient_text(
        self,
        pages: list[dict],
    ) -> bool:
        """Determine whether native PDF extraction produced enough text."""

        total_text = " ".join(
            page.get("text", "")
            for page in pages
        )

        return (
            len(total_text.strip())
            >= self.MIN_TEXT_LENGTH
        )

    def _extract_using_ocr(self) -> list[dict]:
        """Render each PDF page and extract text using Tesseract."""

        pages = []

        page_count = (
            self.pdf_processor.get_page_count()
        )

        for page_number in range(
            1,
            page_count + 1,
        ):
            print(
                f"       OCR page {page_number}/{page_count}..."
            )

            image_path = (
                self.pdf_processor.render_page_as_image(
                    page_number=page_number,
                    output_path=(
                        Path("data/ocr")
                        / f"{self.pdf_path.stem}"
                        f"_page{page_number}.png"
                    ),
                )
            )

            raw_text = self.ocr_processor.extract_text(
                image_path
            )

            normalized_text = self.normalizer.normalize(
                raw_text
            )

            pages.append(
                {
                    "page_number": page_number,
                    "text": normalized_text,
                    "raw_text": raw_text,
                    "extraction_method": "ocr",
                }
            )

        return pages