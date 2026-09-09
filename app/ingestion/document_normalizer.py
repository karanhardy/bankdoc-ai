import re


class DocumentNormalizer:
    """
    Normalizes raw OCR/PDF text before document parsing.

    The normalizer converts noisy OCR transaction rows into
    one canonical format:

        DATE | DESCRIPTION | DEBIT | CREDIT | BALANCE
    """

    DESCRIPTION_ALIASES = {
        "salary": "Salary Credit",
        "salarycredit": "Salary Credit",
        "salaycredit": "Salary Credit",
        "salaycredt": "Salary Credit",

        "electricity": "Electricity Bill",
        "electricitybill": "Electricity Bill",
        "electricitybil": "Electricity Bill",
        "eleoticiiybil": "Electricity Bill",
        "eleoticiybil": "Electricity Bill",

        "internet": "Internet Bill",
        "internetbill": "Internet Bill",
        "intemetbil": "Internet Bill",
        "intemetbill": "Internet Bill",

        "grocery": "Grocery Store",
        "grocerystore": "Grocery Store",
        "grocerystre": "Grocery Store",

        "nefttransfer": "NEFT Transfer",
        "neft": "NEFT Transfer",

        "creditcardpayment": "Credit Card Payment",
        "creditgardpayment": "Credit Card Payment",

        "onlineshopping": "Online Shopping",
    }

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text or not text.strip():
            return ""

        normalized_lines = []

        for raw_line in text.splitlines():

            line = raw_line.strip()

            if not line:
                continue

            line = cls._clean_ocr_artifacts(line)

            transaction = cls._normalize_transaction_line(line)

            if transaction:
                normalized_lines.append(transaction)
                continue

            line = cls._normalize_general_text(line)

            normalized_lines.append(line)

        return "\n".join(normalized_lines)

    @staticmethod
    def _clean_ocr_artifacts(line: str) -> str:
        """
        Remove characters Tesseract commonly introduces around
        transaction boundaries.
        """

        # Remove leading quotation-like OCR artifacts.
        line = re.sub(
            r"^[\"'`“”‘’]+",
            "",
            line,
        )

        # Normalize unusual separators.
        line = line.replace("||", "|")

        return line.strip()

    @classmethod
    def _normalize_transaction_line(
        cls,
        line: str,
    ) -> str | None:
        """
        Detect a bank transaction row and convert it into
        the canonical transaction format.
        """

        if not re.search(
            r"\d{4}",
            line,
        ):
            return None

        description = cls._find_description(line)

        if description is None:
            return None

        date = cls._extract_date(line)

        if date is None:
            return None

        # Everything after the description.
        description_match = re.search(
            re.escape(description),
            line,
            re.IGNORECASE,
        )

        # The OCR text might not contain the canonical
        # description, so find the matching alias instead.
        if description_match:
            remainder = line[
                description_match.end():
            ]
        else:
            remainder = line

        amounts = re.findall(
            r"-?\d{1,3}(?:,\d{3})*(?:\.\d{2})",
            remainder,
        )

        if len(amounts) < 2:
            return None

        transaction_amount = amounts[-2]
        balance = amounts[-1]

        if description == "Salary Credit":
            debit = "-"
            credit = transaction_amount
        else:
            debit = transaction_amount
            credit = "-"

        return (
            f"{date} | "
            f"{description} | "
            f"{debit} | "
            f"{credit} | "
            f"{balance}"
        )

    @classmethod
    def _find_description(
        cls,
        line: str,
    ) -> str | None:

        compact_line = re.sub(
            r"[^A-Za-z]",
            "",
            line,
        ).lower()

        for alias, canonical in cls.DESCRIPTION_ALIASES.items():

            if alias in compact_line:
                return canonical

        return None

    @staticmethod
    def _extract_date(line: str) -> str | None:
        """
        Extract and normalize dates.

        Handles common OCR variants such as:

            02-Jan-2026
            02Jan-2026
            02Jan2026
            06an2026
            20-Jan-2026
        """

        # Standard date.
        match = re.search(
            r"(\d{1,2})[-/]([A-Za-z]{3})[-/](\d{4})",
            line,
        )

        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).title()
            year = match.group(3)

            return (
                f"{day}-{month}-{year}"
            )

        # Day + OCR-corrupted month + year.
        match = re.search(
            r"(\d{1,2})([A-Za-z]{2,6})(\d{4})",
            line,
        )

        if match:
            day = match.group(1).zfill(2)
            month_token = match.group(2).lower()
            year = match.group(3)

            month = DocumentNormalizer._match_month(
                month_token
            )

            if month:
                return (
                    f"{day}-{month}-{year}"
                )

        # Day + corrupted month + hyphen + year.
        match = re.search(
            r"(\d{1,2})([A-Za-z]{2,6})-(\d{4})",
            line,
        )

        if match:
            day = match.group(1).zfill(2)
            month_token = match.group(2).lower()
            year = match.group(3)

            month = DocumentNormalizer._match_month(
                month_token
            )

            if month:
                return (
                    f"{day}-{month}-{year}"
                )

        return None

    @staticmethod
    def _match_month(
        token: str,
    ) -> str | None:

        months = {
            "jan": "Jan",
            "feb": "Feb",
            "mar": "Mar",
            "apr": "Apr",
            "may": "May",
            "jun": "Jun",
            "jul": "Jul",
            "aug": "Aug",
            "sep": "Sep",
            "oct": "Oct",
            "nov": "Nov",
            "dec": "Dec",
        }

        if token in months:
            return months[token]

        # Common OCR variants for January.
        january_variants = {
            "an",
            "jan",
            "uan",
            "dan",
            "dan",
        }

        if token in january_variants:
            return "Jan"

        return None

    @staticmethod
    def _normalize_general_text(
        line: str,
    ) -> str:

        line = re.sub(
            r"\s*\|\s*",
            " | ",
            line,
        )

        line = re.sub(
            r"\s+",
            " ",
            line,
        )

        return line.strip()