import json
from pathlib import Path
from typing import Any

from app.ingestion.pdf_processor import PDFProcessor
from app.ingestion.document_parser import BankStatementParser
from app.storage.bronze import BronzeStorage
from app.storage.silver import SilverStorage
from app.transformation.gold_transformer import GoldTransformer


class DocumentPipeline:
    """
    End-to-end document ingestion pipeline.

    PDF
      ↓
    Text extraction
      ↓
    Bronze
      ↓
    Document parsing
      ↓
    Silver
      ↓
    Gold transformation
      ↓
    Gold
    """

    def __init__(
        self,
        bronze_dir: Path,
        silver_dir: Path,
        gold_dir: Path,
    ):
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

    def process(self, pdf_path: Path) -> dict[str, Any]:
        """
        Process one PDF from ingestion to Gold.
        """

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        print("\n" + "=" * 60)
        print("BANKDOC AI - DOCUMENT PIPELINE")
        print("=" * 60)

        # --------------------------------------------------
        # 1. PDF EXTRACTION
        # --------------------------------------------------

        print("\n[1/5] Extracting PDF...")

        pdf_processor = PDFProcessor(pdf_path)

        pages = pdf_processor.extract_text()

        print(
            f"       Pages extracted: {len(pages)}"
        )

        # --------------------------------------------------
        # 2. BRONZE
        # --------------------------------------------------

        print("\n[2/5] Writing Bronze layer...")

        bronze_file = self.bronze_storage.save(
            source_file=pdf_path,
            pages=pages,
        )

        print(
            f"       Bronze: {bronze_file}"
        )

        # --------------------------------------------------
        # 3. SILVER
        # --------------------------------------------------

        print("\n[3/5] Parsing document...")

        full_text = "\n".join(
            page["text"]
            for page in pages
        )

        parser = BankStatementParser()

        silver_document = parser.parse(
            full_text
        )

        silver_file = self.silver_storage.save(
            source_file=pdf_path,
            parsed_document=silver_document,
        )

        print(
            f"       Document type: "
            f"{silver_document['document_type']}"
        )

        print(
            f"       Transactions: "
            f"{len(silver_document['transactions'])}"
        )

        print(
            f"       Silver: {silver_file}"
        )

        # --------------------------------------------------
        # 4. GOLD
        # --------------------------------------------------

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

        # --------------------------------------------------
        # 5. COMPLETE
        # --------------------------------------------------

        print("\n[5/5] Pipeline completed!")

        print("=" * 60)

        return gold_document


def main() -> None:
    """
    Command-line entry point.
    """

    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python -m app.ingestion.pipeline "
            "<pdf_path>"
        )
        raise SystemExit(1)

    pdf_path = Path(sys.argv[1])

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
        )
    )


if __name__ == "__main__":
    main()