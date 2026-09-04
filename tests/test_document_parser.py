from pathlib import Path

from app.ingestion.document_parser import BankStatementParser
from app.ingestion.pdf_processor import PDFProcessor


PDF_PATH = Path(
    "data/sample_documents/bank_statement_january.pdf"
)


def main() -> None:
    processor = PDFProcessor(PDF_PATH)

    pages = processor.extract_text()

    full_text = "\n".join(
        page["text"]
        for page in pages
    )

    parser = BankStatementParser()

    result = parser.parse(full_text)

    print("\n" + "=" * 60)
    print("PARSED DOCUMENT")
    print("=" * 60)

    print(result)


if __name__ == "__main__":
    main()