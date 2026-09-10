from pathlib import Path

from app.ingestion.document_detector import (
    DocumentDetector,
)
from app.ingestion.document_extractor import (
    DocumentExtractor,
)


DOCUMENTS = [
    Path(
        "data/sample_documents/"
        "bank_statement_january.pdf"
    ),
    Path(
        "data/sample_documents/"
        "electricity_bill_march.pdf"
    ),
]


def main() -> None:

    detector = DocumentDetector()

    print("\n" + "=" * 60)
    print("REAL DOCUMENT DETECTION TEST")
    print("=" * 60)

    for document_path in DOCUMENTS:

        print("\n" + "-" * 60)
        print(
            f"Document: {document_path.name}"
        )

        extractor = DocumentExtractor(
            document_path
        )

        pages = extractor.extract()

        full_text = "\n".join(
            page["text"]
            for page in pages
        )

        result = detector.detect(
            full_text
        )

        print(
            f"Type: {result.document_type.value}"
        )

        print(
            f"Confidence: {result.confidence}"
        )


if __name__ == "__main__":
    main()