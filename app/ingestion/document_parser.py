import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.ingestion.document_normalizer import DocumentNormalizer


class BankStatementParser:
    """
    Parses bank statement text from both:

    1. Native PDF extraction, where table columns may be
       separated across multiple lines.

    2. OCR extraction, where a transaction may appear on
       a single line.

    Canonical transaction structure:

        DATE | DESCRIPTION | DEBIT | CREDIT | BALANCE
    """

    AMOUNT_PATTERN = re.compile(
        r"-?\d{1,3}(?:,\d{3})*(?:\.\d{2})"
    )

    CREDIT_DESCRIPTIONS = {
        "salary credit",
        "interest credit",
        "refund",
    }

    DEBIT_DESCRIPTIONS = {
        "electricity bill",
        "internet bill",
        "grocery store",
        "neft transfer",
        "credit card payment",
        "online shopping",
    }

    DESCRIPTION_ALIASES = {
        "salarycredit": "Salary Credit",
        "salaycredit": "Salary Credit",
        "salaycredt": "Salary Credit",

        "electricitybill": "Electricity Bill",
        "electricitybil": "Electricity Bill",
        "electricitybll": "Electricity Bill",
        "eleoticiiybil": "Electricity Bill",
        "eleoticiybil": "Electricity Bill",

        "internetbill": "Internet Bill",
        "intemetbill": "Internet Bill",
        "intemetbil": "Internet Bill",

        "grocerystore": "Grocery Store",
        "grocerystre": "Grocery Store",

        "nefttransfer": "NEFT Transfer",
        "neft": "NEFT Transfer",

        "creditcardpayment": "Credit Card Payment",
        "creditgardpayment": "Credit Card Payment",
        "creditcardpayrment": "Credit Card Payment",

        "onlineshopping": "Online Shopping",
    }

    def parse(
        self,
        text: str,
    ) -> dict[str, Any]:

        if not text or not text.strip():
            raise ValueError(
                "Cannot parse empty document text."
            )

        normalized_text = DocumentNormalizer.normalize(
            text
        )

        return {
            "document_type": "bank_statement",
            "account_holder": self._extract_field(
                normalized_text,
                r"Account Holder\s+(.+)",
            ),
            "account_number": self._extract_field(
                normalized_text,
                r"Account Number\s+(.+)",
            ),
            "account_type": self._extract_field(
                normalized_text,
                r"Account Type\s+(.+)",
            ),
            "statement_period": (
                self._extract_statement_period(
                    normalized_text
                )
            ),
            "currency": self._extract_field(
                normalized_text,
                r"Currency\s+([A-Z]{3})",
            ),
            "transactions": self._extract_transactions(
                normalized_text
            ),
            "summary": self._extract_summary(
                normalized_text
            ),
        }

    @staticmethod
    def _extract_field(
        text: str,
        pattern: str,
    ) -> str | None:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

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

        try:
            start_date = datetime.strptime(
                match.group(1),
                "%d-%b-%Y",
            ).date()

            end_date = datetime.strptime(
                match.group(2),
                "%d-%b-%Y",
            ).date()

        except ValueError:
            return None

        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }

    # =========================================================
    # TRANSACTION EXTRACTION
    # =========================================================

    def _extract_transactions(
        self,
        text: str,
    ) -> list[dict[str, Any]]:

        # First handle OCR/native layouts where a complete
        # transaction exists on one line.
        transactions = (
            self._extract_transactions_from_lines(
                text
            )
        )

        if transactions:
            return transactions

        # Native PDF extraction can split table cells over
        # multiple lines. Fall back to parsing the complete
        # text stream.
        return self._extract_transactions_from_stream(
            text
        )

    # =========================================================
    # METHOD 1 — COMPLETE TRANSACTION ON ONE LINE
    # =========================================================

    def _extract_transactions_from_lines(
        self,
        text: str,
    ) -> list[dict[str, Any]]:

        transactions = []

        date_pattern = re.compile(
            r"^[\"'`“”‘’\s]*"
            r"(\d{2}-[A-Za-z]{3}-\d{4})\b"
        )

        for raw_line in text.splitlines():

            line = raw_line.strip()

            if not line:
                continue

            date_match = date_pattern.match(line)

            if not date_match:
                continue

            description = self._extract_description(
                line
            )

            if description is None:
                continue

            amount_matches = (
                self.AMOUNT_PATTERN.findall(
                    line[date_match.end():]
                )
            )

            if len(amount_matches) < 2:
                continue

            transaction_amount_text = (
                amount_matches[-2]
            )

            balance_text = amount_matches[-1]

            transaction_amount = self._parse_amount(
                transaction_amount_text
            )

            balance = self._parse_amount(
                balance_text
            )

            if (
                transaction_amount is None
                or balance is None
            ):
                continue

            debit, credit = (
                self._classify_transaction(
                    description,
                    transaction_amount,
                )
            )

            transactions.append(
                {
                    "date": self._parse_date(
                        date_match.group(1)
                    ),
                    "description": description,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance,
                }
            )

        return transactions

    # =========================================================
    # METHOD 2 — NATIVE PDF STREAM
    # =========================================================

    def _extract_transactions_from_stream(
        self,
        text: str,
    ) -> list[dict[str, Any]]:

        transactions = []

        # Native pypdf output can look like:
        #
        # Date
        # Description
        # Debit
        # Credit
        # Balance
        # 02-Jan-2026
        # Salary Credit
        # -
        # 85,000.00
        # 125,000.00
        #
        # The regex below intentionally allows arbitrary
        # whitespace between these pieces.

        amount_pattern = (
            r"-?"
            r"\d{1,3}"
            r"(?:,\d{3})*"
            r"(?:\.\d{2})"
        )

        description_pattern = (
            r"(Salary\s+Credit"
            r"|Electricity\s+Bill"
            r"|Internet\s+Bill"
            r"|Grocery\s+Store"
            r"|NEFT\s+Transfer"
            r"|Credit\s+Card\s+Payment"
            r"|Online\s+Shopping)"
        )

        pattern = re.compile(
            rf"(\d{{2}}-[A-Za-z]{{3}}-\d{{4}})"
            rf"\s+"
            rf"{description_pattern}"
            rf"\s+"
            rf"(-|{amount_pattern})"
            rf"\s+"
            rf"(-|{amount_pattern})"
            rf"\s+"
            rf"({amount_pattern})",
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):

            date_text = match.group(1)
            description = self._canonical_description(
                match.group(2)
            )

            debit_text = match.group(3)
            credit_text = match.group(4)
            balance_text = match.group(5)

            debit = self._parse_amount(
                debit_text
            )

            credit = self._parse_amount(
                credit_text
            )

            balance = self._parse_amount(
                balance_text
            )

            # If the native PDF explicitly supplied debit
            # and credit columns, trust them.
            if debit is not None or credit is not None:
                pass

            else:
                transaction_amount = None

                if debit_text != "-":
                    transaction_amount = (
                        self._parse_amount(
                            debit_text
                        )
                    )

                elif credit_text != "-":
                    transaction_amount = (
                        self._parse_amount(
                            credit_text
                        )
                    )

                if transaction_amount is not None:
                    debit, credit = (
                        self._classify_transaction(
                            description,
                            transaction_amount,
                        )
                    )

            if balance is None:
                continue

            parsed_date = self._parse_date(
                date_text
            )

            if parsed_date is None:
                continue

            transactions.append(
                {
                    "date": parsed_date,
                    "description": description,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance,
                }
            )

        return transactions

    # =========================================================
    # DESCRIPTION HANDLING
    # =========================================================

    def _extract_description(
        self,
        line: str,
    ) -> str | None:

        line_without_date = re.sub(
            r"^[\"'`“”‘’\s]*"
            r"\d{1,2}[-A-Za-z/]+\d{4}",
            "",
            line,
            count=1,
            flags=re.IGNORECASE,
        )

        compact_line = re.sub(
            r"[^A-Za-z]",
            "",
            line_without_date,
        ).lower()

        for alias, canonical in (
            self.DESCRIPTION_ALIASES.items()
        ):
            if alias in compact_line:
                return canonical

        return None

    def _canonical_description(
        self,
        description: str,
    ) -> str:

        compact = re.sub(
            r"[^A-Za-z]",
            "",
            description,
        ).lower()

        for alias, canonical in (
            self.DESCRIPTION_ALIASES.items()
        ):
            if alias == compact:
                return canonical

        return description.strip()

    # =========================================================
    # DEBIT / CREDIT CLASSIFICATION
    # =========================================================

    def _classify_transaction(
        self,
        description: str,
        amount: float,
    ) -> tuple[float | None, float | None]:

        normalized = description.lower().strip()

        # Salary Credit is income.
        if normalized in self.CREDIT_DESCRIPTIONS:
            return None, amount

        # Credit Card Payment is explicitly a debit.
        if normalized in self.DEBIT_DESCRIPTIONS:
            return amount, None

        if "credit card payment" in normalized:
            return amount, None

        if "salary" in normalized:
            return None, amount

        # Conservative fallback.
        return amount, None

    # =========================================================
    # UTILITIES
    # =========================================================

    @staticmethod
    def _parse_date(
        value: str,
    ) -> str | None:

        try:
            return datetime.strptime(
                value,
                "%d-%b-%Y",
            ).date().isoformat()

        except ValueError:
            return None

    @staticmethod
    def _parse_amount(
        value: str,
    ) -> float | None:

        if not value or value == "-":
            return None

        try:
            return float(
                Decimal(
                    value.replace(",", "")
                )
            )

        except InvalidOperation:
            return None

    # =========================================================
    # SUMMARY
    # =========================================================

    def _extract_summary(
        self,
        text: str,
    ) -> dict[str, float | None]:

        return {
            "opening_balance": (
                self._extract_summary_amount(
                    text,
                    "Opening Balance",
                )
            ),
            "total_credits": (
                self._extract_summary_amount(
                    text,
                    "Total Credits",
                )
            ),
            "total_debits": (
                self._extract_summary_amount(
                    text,
                    "Total Debits",
                )
            ),
            "closing_balance": (
                self._extract_summary_amount(
                    text,
                    "Closing Balance",
                )
            ),
        }

    def _extract_summary_amount(
        self,
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

        return self._parse_amount(
            match.group(1)
        )