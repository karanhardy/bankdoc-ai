from app.ingestion.document_detector import (
    DocumentDetector,
    DocumentType,
)


def test_bank_statement() -> None:
    text = """
    EVEREST NATIONAL BANK
    Monthly Bank Statement

    Account Holder Alex Morgan
    Account Number XXXX-XXXX-4582
    Statement Period 01-Jan-2026 to 31-Jan-2026

    Date Description Debit Credit Balance
    """

    detector = DocumentDetector()

    result = detector.detect(text)

    print(
        f"Document Type: {result.document_type.value}"
    )

    print(
        f"Confidence: {result.confidence}"
    )

    assert (
        result.document_type
        == DocumentType.BANK_STATEMENT
    )


def test_electricity_bill() -> None:
    text = """
    EVEREST POWER COMPANY
    Electricity Bill

    Consumer Number EB123456
    Meter Number MTR7890
    Billing Period March 2026
    Units Consumed 245
    Amount Due 2450.50
    Due Date 10-Apr-2026
    """

    detector = DocumentDetector()

    result = detector.detect(text)

    print(
        f"Document Type: {result.document_type.value}"
    )

    print(
        f"Confidence: {result.confidence}"
    )

    assert (
        result.document_type
        == DocumentType.ELECTRICITY_BILL
    )


def main() -> None:
    print("\n" + "=" * 60)
    print("DOCUMENT DETECTOR TEST")
    print("=" * 60)

    test_bank_statement()

    print()

    test_electricity_bill()

    print("\nAll detector tests passed.")


if __name__ == "__main__":
    main()