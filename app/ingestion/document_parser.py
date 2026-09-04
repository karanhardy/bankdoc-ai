import re
from datetime import datetime
from decimal import Decimal
from typing import Any


class BankStatementParser:
    """Parses extracted bank statement text into structured data."""

    DATE_PATTERN = re.compile(
        r"\b(\d{2}-[A-Za-z]{3}-\d{4})\b"
    )

    AMOUNT_PATTERN = re.compile(
        r"\b\d{1,3}(?:,\d{3})*(?:\.\d{2})\b"
    )

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse raw PDF/OCR text into a structured bank statement.
        """

        if not text or not text.strip():
            raise ValueError("Cannot parse empty document text.")

        normalized_text = self._normalize_text(text)

        return {
            "document_type": "bank_statement",
            "account_holder": self._extract_field(
                normalized_text,
                r"Account Holder\s+(.+)"
            ),
            "account_number": self._extract_field(
                normalized_text,
                r"Account Number\s+(.+)"
            ),
            "account_type": self._extract_field(
                normalized_text,
                r"Account Type\s+(.+)"
            ),
            "statement_period": self._extract_statement_period(
                normalized_text
            ),
            "currency": self._extract_field(
                normalized_text,
                r"Currency\s+([A-Z]{3})"
            ),
            "transactions": self._extract_transactions(
                normalized_text
            ),
            "summary": self._extract_summary(
                normalized_text
            ),
        }

    @staticmethod
    def _normalize_text(text: str) -> str:
        lines = []

        for line in text.splitlines():
            line = line.strip()

            if line:
                lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _extract_field(text: str, pattern: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            return None

        return match.group(1).strip()

    @staticmethod
    def _extract_statement_period(
        text: str,
    ) -> dict[str, str] | None:

        pattern = (
            r"Statement Period\s+"
            r"(\d{2}-[A-Za-z]{3}-\d{4})\s+to\s+"
            r"(\d{2}-[A-Za-z]{3}-\d{4})"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        start_date = datetime.strptime(
            match.group(1),
            "%d-%b-%Y",
        ).date()

        end_date = datetime.strptime(
            match.group(2),
            "%d-%b-%Y",
        ).date()

        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }

    def _extract_transactions(
        self,
        text: str,
    ) -> list[dict[str, Any]]:

        transactions = []

        pattern = re.compile(
            r"(\d{2}-[A-Za-z]{3}-\d{4})\s+"
            r"(.+?)\s+"
            r"(-|\d{1,3}(?:,\d{3})*\.\d{2})\s+"
            r"(-|\d{1,3}(?:,\d{3})*\.\d{2})\s+"
            r"(\d{1,3}(?:,\d{3})*\.\d{2})"
        )

        for match in pattern.finditer(text):

            date_text = match.group(1)
            description = match.group(2).strip()

            debit = self._parse_amount(match.group(3))
            credit = self._parse_amount(match.group(4))
            balance = self._parse_amount(match.group(5))

            date_value = datetime.strptime(
                date_text,
                "%d-%b-%Y",
            ).date()

            transactions.append(
                {
                    "date": date_value.isoformat(),
                    "description": description,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance,
                }
            )

        return transactions

    def _extract_summary(
        self,
        text: str,
    ) -> dict[str, float | None]:

        return {
            "opening_balance": self._extract_summary_amount(
                text,
                "Opening Balance",
            ),
            "total_credits": self._extract_summary_amount(
                text,
                "Total Credits",
            ),
            "total_debits": self._extract_summary_amount(
                text,
                "Total Debits",
            ),
            "closing_balance": self._extract_summary_amount(
                text,
                "Closing Balance",
            ),
        }

    @staticmethod
    def _extract_summary_amount(
        text: str,
        field_name: str,
    ) -> float | None:

        pattern = (
            re.escape(field_name)
            + r"\s+"
            + r"(\d{1,3}(?:,\d{3})*\.\d{2})"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        return float(
            Decimal(
                match.group(1).replace(",", "")
            )
        )

    @staticmethod
    def _parse_amount(
        value: str,
    ) -> float | None:

        if value == "-":
            return None

        return float(
            Decimal(
                value.replace(",", "")
            )
        )