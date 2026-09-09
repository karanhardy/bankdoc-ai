import re


class DocumentNormalizer:
    """Normalizes raw OCR/PDF text before document parsing."""

    OCR_REPLACEMENTS = {
        "SalayCredit": "Salary Credit",
        "Salay Credit": "Salary Credit",

        "Electricity Bil": "Electricity Bill",
        "Electricity Bll": "Electricity Bill",

        "intemet Bil": "Internet Bill",
        "intemet Bill": "Internet Bill",

        "GroceryStore": "Grocery Store",
        "Grocery Stre": "Grocery Store",

        "Credit Gard Payment": "Credit Card Payment",
        "Credit Card Payrment": "Credit Card Payment",

        "Online Shopping": "Online Shopping",
    }

    TRANSACTION_DESCRIPTIONS = (
        "Salary Credit",
        "Electricity Bill",
        "Internet Bill",
        "Grocery Store",
        "NEFT Transfer",
        "Credit Card Payment",
        "Online Shopping",
    )

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text or not text.strip():
            return ""

        text = cls._clean_lines(text)
        text = cls._fix_common_ocr_errors(text)
        text = cls._normalize_dates(text)
        text = cls._normalize_transaction_lines(text)
        text = cls._normalize_separators(text)
        text = cls._normalize_amount_spacing(text)

        return text.strip()

    @staticmethod
    def _clean_lines(text: str) -> str:
        lines = []

        for line in text.splitlines():
            line = line.strip()

            if line:
                lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _normalize_dates(text: str) -> str:
        """
        Convert common OCR date variations into DD-Mon-YYYY.
        """

        # 02Jan2026 -> 02-Jan-2026
        text = re.sub(
            r"\b(\d{2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{4})\b",
            r"\1-\2-\3",
            text,
            flags=re.IGNORECASE,
        )

        # 02Jan-2026 -> 02-Jan-2026
        text = re.sub(
            r"\b(\d{2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{4})\b",
            r"\1-\2-\3",
            text,
            flags=re.IGNORECASE,
        )

        return text

    @classmethod
    def _fix_common_ocr_errors(cls, text: str) -> str:
        for incorrect, correct in cls.OCR_REPLACEMENTS.items():
            text = re.sub(
                re.escape(incorrect),
                correct,
                text,
                flags=re.IGNORECASE,
            )

        return text

    @classmethod
    def _normalize_transaction_lines(cls, text: str) -> str:
        """
        Convert OCR transaction rows into the canonical format:

        DATE | DESCRIPTION | DEBIT | CREDIT | BALANCE
        """

        normalized_lines = []

        for line in text.splitlines():

            # Skip lines that don't contain a known transaction description.
            description = None

            for known_description in cls.TRANSACTION_DESCRIPTIONS:
                if known_description.lower() in line.lower():
                    description = known_description
                    break

            if not description:
                normalized_lines.append(line)
                continue

            # Extract date.
            date_match = re.search(
                r"\b\d{2}-[A-Za-z]{3}-\d{4}\b",
                line,
            )

            if not date_match:
                normalized_lines.append(line)
                continue

            date_text = date_match.group(0)

            # Everything after the description.
            description_position = line.lower().find(
                description.lower()
            )

            remainder = line[
                description_position
                + len(description):
            ]

            # Extract all monetary amounts.
            amounts = re.findall(
                r"\d{1,3}(?:,\d{3})*\.\d{2}",
                remainder,
            )

            if len(amounts) < 2:
                normalized_lines.append(line)
                continue

            # Last amount is always the balance.
            balance = amounts[-1]

            # The other amount is the transaction amount.
            transaction_amount = amounts[-2]

            # Determine debit/credit from description.
            if description == "Salary Credit":
                debit = "-"
                credit = transaction_amount

            else:
                debit = transaction_amount
                credit = "-"

            normalized_lines.append(
                (
                    f"{date_text} | "
                    f"{description} | "
                    f"{debit} | "
                    f"{credit} | "
                    f"{balance}"
                )
            )

        return "\n".join(normalized_lines)

    @staticmethod
    def _normalize_separators(text: str) -> str:
        """
        Normalize OCR-generated separators.
        """

        text = re.sub(
            r"\s*\|\s*",
            " | ",
            text,
        )

        # Collapse repeated pipes.
        text = re.sub(
            r"(?:\s*\|\s*){2,}",
            " | ",
            text,
        )

        return text

    @staticmethod
    def _normalize_amount_spacing(text: str) -> str:
        """
        Normalize spaces around negative amounts.
        """

        text = re.sub(
            r"-\s+(\d[\d,]*\.\d{2})",
            r"-\1",
            text,
        )

        return text