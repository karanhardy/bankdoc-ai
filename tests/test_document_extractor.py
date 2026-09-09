from pathlib import Path

from app.ingestion.document_extractor import (
    DocumentExtractor,
)


PDF_PATH = Path(
    "data/sample_documents/"
    "bank_statement_january_scanned.pdf"
)


def main() -> None:

    print("\n" + "=" * 60)
    print("DOCUMENT EXTRACTOR OCR TEST")
    print("=" * 60)

    extractor = DocumentExtractor(PDF_PATH)

    pages = extractor.extract()

    print("\n" + "=" * 60)
    print("RAW EXTRACTION RESULT")
    print("=" * 60)

    for page in pages:

        print(
            f"\nPAGE {page['page_number']}"
        )

        print(
            f"Method: "
            f"{page['extraction_method']}"
        )

        print(
            f"Characters: "
            f"{len(page['text'])}"
        )

        print("-" * 60)

        print(page["text"])

        print("-" * 60)


if __name__ == "__main__":
    main()