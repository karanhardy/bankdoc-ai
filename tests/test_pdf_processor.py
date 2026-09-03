from pathlib import Path

from app.ingestion.pdf_processor import PDFProcessor


PDF_PATH = Path(
    "data/sample_documents/bank_statement_january.pdf"
)


def main() -> None:
    processor = PDFProcessor(PDF_PATH)

    print(f"PDF: {PDF_PATH}")
    print(f"Pages: {processor.get_page_count()}")

    pages = processor.extract_text()

    for page in pages:
        print("\n" + "=" * 60)
        print(f"PAGE {page['page_number']}")
        print("=" * 60)
        print(page["text"])


if __name__ == "__main__":
    main()