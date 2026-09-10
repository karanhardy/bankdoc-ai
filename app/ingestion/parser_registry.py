from typing import Any, Protocol

from app.ingestion.document_detector import DocumentType
from app.ingestion.document_parser import BankStatementParser
from app.ingestion.electricity_bill_parser import (
    ElectricityBillParser,
)


class DocumentParser(Protocol):
    """Interface that every document parser must implement."""

    def parse(
        self,
        text: str,
    ) -> dict[str, Any]:
        ...


class ParserRegistry:
    """
    Maps document types to their corresponding parsers.

    Adding support for a new document type should only require
    registering its parser here.
    """

    def __init__(self) -> None:
        self._parsers: dict[
            DocumentType,
            DocumentParser,
        ] = {}

        self.register(
            DocumentType.BANK_STATEMENT,
            BankStatementParser(),
        )

        self.register(
            DocumentType.ELECTRICITY_BILL,
            ElectricityBillParser(),
        )

    def register(
        self,
        document_type: DocumentType,
        parser: DocumentParser,
    ) -> None:
        """Register a parser for a document type."""

        self._parsers[document_type] = parser

    def get(
        self,
        document_type: DocumentType,
    ) -> DocumentParser:
        """Return the parser for a document type."""

        parser = self._parsers.get(
            document_type
        )

        if parser is None:
            raise ValueError(
                "No parser registered for document type: "
                f"{document_type.value}"
            )

        return parser

    def parse(
        self,
        document_type: DocumentType,
        text: str,
    ) -> dict[str, Any]:
        """Find the correct parser and parse the document."""

        parser = self.get(document_type)

        return parser.parse(text)