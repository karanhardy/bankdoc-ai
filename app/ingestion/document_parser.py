import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.ingestion.document_normalizer import DocumentNormalizer


class BankStatementParser:
    """
    Parses normalized bank-statement text into structured data.

    Expected transaction format:

        DATE | DESCRIPTION | DEBIT | CREDIT | BALANCE

    The parser is intentionally tolerant of OCR output because OCR
    may introduce minor formatting differences.
    """

    DATE_PATTERN = re.compile(
        r"\b(\d{2}-[A-Za-z]{3}-\d{4})\b"
    )

    AMOUNT_PATTERN = re.compile(
        r"-?\d{1,3}(?:,\d{3})*(?:\.\d{2})"
    )

    # These descriptions are classified explicitly.
    # Do NOT use a generic "credit" check because
    # "Credit Card Payment" is a debit transaction.
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

    # OCR variations mapped to canonical descriptions.
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
        "grocerystore": "Grocery Store",

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
        """
        Parse raw or normalized bank-statement text.
        """

        if not text or not text.strip():
            raise ValueError(
                "Cannot parse empty document text."
            )

        # Normalizing here makes the parser safe to use
        # independently as well as through DocumentExtractor.
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

    def _extract_transactions(
        self,
        text: str,
    ) -> list[dict[str, Any]]:

        transactions: list[dict[str, Any]] = []

        for raw_line in text.splitlines():

            line = raw_line.strip()

            if not line:
                continue

            transaction = self._parse_transaction_line(
                line
            )

            if transaction is not None:
                transactions.append(
                    transaction
                )

        return transactions

    def _parse_transaction_line(
        self,
        line: str,
    ) -> dict[str, Any] | None:

        # ---------------------------------------------------------
        # 1. Extract date
        # ---------------------------------------------------------

        date_match = re.match(
            r"^[\"'`“”‘’\s]*"
            r"(\d{2}-[A-Za-z]{3}-\d{4})\b",
            line,
        )

        if not date_match:
            return None

        date_text = date_match.group(1)

        try:
            date_value = datetime.strptime(
                date_text,
                "%d-%b-%Y",
            ).date()

        except ValueError:
            return None

        # ---------------------------------------------------------
        # 2. Identify transaction description
        # ---------------------------------------------------------

        description = self._extract_description(
            line
        )

        if description is None:
            return None

        # ---------------------------------------------------------
        # 3. Extract monetary values
        # ---------------------------------------------------------

        remainder = line[date_match.end():]

        amount_matches = self.AMOUNT_PATTERN.findall(
            remainder
        )

        if len(amount_matches) < 2:
            return None

        # For a bank statement:
        #
        #   transaction amount + balance
        #
        # are normally the final two meaningful amounts.
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

        if transaction_amount is None:
            return None

        if balance is None:
            return None

        # ---------------------------------------------------------
        # 4. Determine debit / credit explicitly
        # ---------------------------------------------------------

        debit: float | None = None
        credit: float | None = None

        normalized_description = (
            description.lower().strip()
        )

        # Explicitly classify credits first.
        if normalized_description in (
            self.CREDIT_DESCRIPTIONS
        ):
            credit = transaction_amount

        # Explicitly classify known debits.
        elif normalized_description in (
            self.DEBIT_DESCRIPTIONS
        ):
            debit = transaction_amount

        # Handle names containing the word "credit"
        # without incorrectly treating Credit Card Payment
        # as income.
        elif (
            "credit card payment"
            in normalized_description
        ):
            debit = transaction_amount

        elif (
            "salary"
            in normalized_description
        ):
            credit = transaction_amount

        else:
            # Conservative fallback:
            # If we can't confidently classify it,
            # preserve it as a debit rather than inventing income.
            debit = transaction_amount

        return {
            "date": date_value.isoformat(),
            "description": description,
            "debit": debit,
            "credit": credit,
            "balance": balance,
        }

    def _extract_description(
        self,
        line: str,
    ) -> str | None:
        """
        Find a known transaction description in the line
        and return its canonical form.
        """

        # Remove the date and OCR separators from the line.
        line_without_date = re.sub(
            r"^[\"'`“”‘’\s]*"
            r"\d{1,2}[-A-Za-z/]+\d{4}",
            "",
            line,
            count=1,
            flags=re.IGNORECASE,
        )

        # Create a compact representation so OCR spacing and
        # separator errors don't prevent matching.
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

    @staticmethod
    def _parse_amount(
        value: str,
    ) -> float | None:

        if not value:
            return None

        value = value.strip()

        # OCR sometimes surrounds values with
        # punctuation. Keep only the actual number.
        value = value.replace(",", "")

        try:
            amount = Decimal(value)

        except InvalidOperation:
            return None

        return float(amount)