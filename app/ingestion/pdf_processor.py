from pathlib import Path
import pymupdf
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

    def render_page_as_image(
            self,
            page_number: int,
            output_path: Path,
            dpi: int = 200,
    ) -> Path:
        """
        Render a PDF page as an image.

        Args:
            page_number: 1-based page number.
            output_path: Where the image should be saved.
            dpi: Rendering resolution.

        Returns:
            Path to the generated image.
        """

        if page_number < 1:
            raise ValueError("Page number must be >= 1.")

        reader = pymupdf.open(str(self.file_path))

        try:
            if page_number > len(reader):
                raise ValueError(
                    f"Page {page_number} does not exist. "
                    f"PDF contains {len(reader)} pages."
                )

            page = reader[page_number - 1]

            scale = dpi / 72

            matrix = pymupdf.Matrix(scale, scale)

            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False,
            )

            output_path = Path(output_path)
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            pixmap.save(str(output_path))

            return output_path

        finally:
            reader.close()