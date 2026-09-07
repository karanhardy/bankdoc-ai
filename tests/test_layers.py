from pathlib import Path
import json

from app.ingestion.pdf_processor import PDFProcessor
from app.ingestion.document_parser import BankStatementParser
from app.storage.bronze import BronzeStorage
from app.storage.silver import SilverStorage
from app.transformation.gold_transformer import GoldTransformer


PDF_PATH = Path(
    "data/sample_documents/bank_statement_january.pdf"
)

BRONZE_PATH = Path("data/bronze")
SILVER_PATH = Path("data/silver")
GOLD_PATH = Path("data/gold")


def main() -> None:

    # --------------------------------------------------
    # 1. Extract raw document text
    # --------------------------------------------------

    print("\n[1] Extracting PDF text...")

    pdf_processor = PDFProcessor(PDF_PATH)

    pages = pdf_processor.extract_text()

    print(f"Pages extracted: {len(pages)}")


    # --------------------------------------------------
    # 2. BRONZE
    # --------------------------------------------------

    print("\n[2] Saving Bronze...")

    bronze_storage = BronzeStorage(BRONZE_PATH)

    bronze_file = bronze_storage.save(
        source_file=PDF_PATH,
        pages=pages,
    )

    print(f"Bronze file: {bronze_file}")


    # --------------------------------------------------
    # 3. Parse document
    # --------------------------------------------------

    print("\n[3] Parsing document...")

    full_text = "\n".join(
        page["text"]
        for page in pages
    )

    parser = BankStatementParser()

    silver_document = parser.parse(full_text)

    print(
        f"Document type: "
        f"{silver_document['document_type']}"
    )

    print(
        f"Transactions: "
        f"{len(silver_document['transactions'])}"
    )


    # --------------------------------------------------
    # 4. SILVER
    # --------------------------------------------------

    print("\n[4] Saving Silver...")

    silver_storage = SilverStorage(SILVER_PATH)

    silver_file = silver_storage.save(
        source_file=PDF_PATH,
        parsed_document=silver_document,
    )

    print(f"Silver file: {silver_file}")


    # --------------------------------------------------
    # 5. GOLD
    # --------------------------------------------------

    print("\n[5] Creating Gold...")

    gold_transformer = GoldTransformer()

    gold_document = gold_transformer.transform(
        silver_document
    )

    gold_file = (
        GOLD_PATH
        / f"{PDF_PATH.stem}.json"
    )

    GOLD_PATH.mkdir(
        parents=True,
        exist_ok=True,
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

    print(f"Gold file: {gold_file}")


    # --------------------------------------------------
    # 6. Display Gold
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("GOLD DOCUMENT")
    print("=" * 60)

    print(
        json.dumps(
            gold_document,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()