from pathlib import Path

from app.ingestion.document_detector import (
    DocumentDetector,
)
from app.ingestion.document_extractor import (
    DocumentExtractor,
)
from app.ingestion.parser_registry import (
    ParserRegistry,
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
    registry = ParserRegistry()

    print("\n" + "=" * 60)
    print("PARSER REGISTRY TEST")
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

        detection = detector.detect(
            full_text
        )

        print(
            f"Detected type: "
            f"{detection.document_type.value}"
        )

        parser = registry.get(
            detection.document_type
        )

        print(
            f"Selected parser: "
            f"{parser.__class__.__name__}"
        )

        parsed = registry.parse(
            detection.document_type,
            full_text,
        )

        print(
            f"Parsed type: "
            f"{parsed['document_type']}"
        )

    print("\n" + "=" * 60)
    print("PARSER REGISTRY TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()