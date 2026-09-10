from pathlib import Path

from app.ingestion.document_extractor import (
    DocumentExtractor,
)
from app.ingestion.electricity_bill_parser import (
    ElectricityBillParser,
)


PDF_PATH = Path(
    "data/sample_documents/"
    "electricity_bill_march.pdf"
)


def main() -> None:

    extractor = DocumentExtractor(
        PDF_PATH
    )

    pages = extractor.extract()

    full_text = "\n".join(
        page["text"]
        for page in pages
    )

    parser = ElectricityBillParser()

    result = parser.parse(
        full_text
    )

    print("\n" + "=" * 60)
    print("ELECTRICITY BILL PARSER TEST")
    print("=" * 60)

    print(result)


if __name__ == "__main__":
    main()