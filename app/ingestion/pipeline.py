import json
import sys
from pathlib import Path
from typing import Any

from app.ingestion.document_detector import (
    DocumentDetector,
    DocumentType,
)
from app.ingestion.document_extractor import (
    DocumentExtractor,
)
from app.ingestion.parser_registry import (
    ParserRegistry,
)
from app.storage.bronze import BronzeStorage
from app.storage.silver import SilverStorage
from app.transformation.gold_transformer import GoldTransformer


class DocumentPipeline:
    """
    End-to-end BankDoc document ingestion pipeline.

    Flow:

        PDF
         ↓
        DocumentExtractor
         ↓
        Bronze
         ↓
        DocumentDetector
         ↓
        ParserRegistry
         ↓
        Silver
         ↓
        GoldTransformer
         ↓
        Gold
    """

    def __init__(
        self,
        bronze_dir: Path,
        silver_dir: Path,
        gold_dir: Path,
    ) -> None:

        self.bronze_storage = BronzeStorage(
            bronze_dir
        )

        self.silver_storage = SilverStorage(
            silver_dir
        )

        self.gold_transformer = GoldTransformer()

        self.gold_dir = Path(gold_dir)

        self.gold_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.document_detector = DocumentDetector()

        self.parser_registry = ParserRegistry()

    def process(
        self,
        pdf_path: Path,
    ) -> dict[str, Any]:

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        if not pdf_path.is_file():
            raise ValueError(
                f"Expected a file: {pdf_path}"
            )

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file, got: "
                f"{pdf_path.suffix}"
            )

        print("\n" + "=" * 60)
        print("BANKDOC AI - DOCUMENT PIPELINE")
        print("=" * 60)

        # ==================================================
        # 1. DOCUMENT EXTRACTION
        # ==================================================

        print("\n[1/5] Extracting PDF...")

        document_extractor = DocumentExtractor(
            pdf_path
        )

        pages = document_extractor.extract()

        if not pages:
            raise ValueError(
                "No pages were extracted from the document."
            )

        print(
            f"       Pages extracted: {len(pages)}"
        )

        # ==================================================
        # 2. BRONZE
        # ==================================================

        print("\n[2/5] Writing Bronze layer...")

        bronze_file = self.bronze_storage.save(
            source_file=pdf_path,
            pages=pages,
        )

        print(
            f"       Bronze: {bronze_file}"
        )

        # ==================================================
        # 3. DETECTION + SILVER
        # ==================================================

        print("\n[3/5] Parsing document...")

        full_text = "\n".join(
            page.get("text", "")
            for page in pages
        )

        if not full_text.strip():
            raise ValueError(
                "Document extraction produced no text."
            )

        # ----------------------------------------------
        # Detect document type
        # ----------------------------------------------

        detection = self.document_detector.detect(
            full_text
        )

        print(
            f"       Document type: "
            f"{detection.document_type.value}"
        )

        print(
            f"       Detection confidence: "
            f"{detection.confidence}"
        )

        if (
            detection.document_type
            == DocumentType.UNKNOWN
        ):
            raise ValueError(
                "Unable to determine document type."
            )

        # ----------------------------------------------
        # Select parser
        # ----------------------------------------------

        parser = self.parser_registry.get(
            detection.document_type
        )

        print(
            f"       Parser: "
            f"{parser.__class__.__name__}"
        )

        # ----------------------------------------------
        # Parse document
        # ----------------------------------------------

        silver_document = self.parser_registry.parse(
            detection.document_type,
            full_text,
        )

        # ----------------------------------------------
        # Save Silver
        # ----------------------------------------------

        silver_file = self.silver_storage.save(
            source_file=pdf_path,
            parsed_document=silver_document,
        )

        print(
            f"       Silver: {silver_file}"
        )

        # ==================================================
        # 4. GOLD
        # ==================================================

        print("\n[4/5] Creating Gold layer...")

        gold_document = (
            self.gold_transformer.transform(
                silver_document
            )
        )

        gold_file = (
            self.gold_dir
            / f"{pdf_path.stem}.json"
        )

        with gold_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                gold_document,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"       Gold: {gold_file}"
        )

        # ==================================================
        # 5. COMPLETE
        # ==================================================

        print("\n[5/5] Pipeline completed!")

        print("=" * 60)

        return gold_document


def main() -> None:
    """
    Command-line entry point.

    Usage:

        python -m app.ingestion.pipeline <pdf_path>
    """

    if len(sys.argv) != 2:

        print(
            "Usage: "
            "python -m app.ingestion.pipeline "
            "<pdf_path>"
        )

        raise SystemExit(1)

    pdf_path = Path(
        sys.argv[1]
    )

    pipeline = DocumentPipeline(
        bronze_dir=Path("data/bronze"),
        silver_dir=Path("data/silver"),
        gold_dir=Path("data/gold"),
    )

    gold_document = pipeline.process(
        pdf_path
    )

    print("\nGOLD RESULT")
    print("-" * 60)

    print(
        json.dumps(
            gold_document,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()