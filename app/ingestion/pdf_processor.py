from pathlib import Path

from pypdf import PdfReader


class PDFProcessor:
    """Handles PDF loading and basic text extraction."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {self.file_path}"
            )

        if self.file_path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file, got: {self.file_path.suffix}"
            )

    def get_page_count(self) -> int:
        """Return the number of pages in the PDF."""

        reader = PdfReader(str(self.file_path))

        return len(reader.pages)

    def extract_text(self) -> list[dict]:
        """
        Extract embedded text from every PDF page.

        Returns:
            A list containing page-level extracted text.
        """

        reader = PdfReader(str(self.file_path))

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            pages.append(
                {
                    "page_number": page_number,
                    "text": text.strip(),
                }
            )

        return pages