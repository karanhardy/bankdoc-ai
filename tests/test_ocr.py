from pathlib import Path

from app.ingestion.ocr import OCRProcessor
from app.ingestion.pdf_processor import PDFProcessor


PDF_PATH = Path(
    "data/sample_documents/bank_statement_january.pdf"
)

IMAGE_PATH = Path(
    "data/sample_documents/bank_statement_january_page1.png"
)


def main() -> None:
    pdf_processor = PDFProcessor(PDF_PATH)

    print("Rendering PDF page as image...")

    image_path = pdf_processor.render_page_as_image(
        page_number=1,
        output_path=IMAGE_PATH,
        dpi=300,
    )

    print(f"Created image: {image_path}")

    print("\nRunning OCR...")

    ocr_processor = OCRProcessor()

    text = ocr_processor.extract_text(image_path)

    print("\n" + "=" * 60)
    print("OCR RESULT")
    print("=" * 60)

    print(text)


if __name__ == "__main__":
    main()