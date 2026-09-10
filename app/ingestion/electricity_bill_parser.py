import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


class ElectricityBillParser:
    """Parses structured electricity bill text."""

    def parse(
        self,
        text: str,
    ) -> dict[str, Any]:

        if not text or not text.strip():
            raise ValueError(
                "Cannot parse empty electricity bill."
            )

        return {
            "document_type": "electricity_bill",
            "customer_name": self._extract_field(
                text,
                r"Customer Name\s+(.+)",
            ),
            "consumer_number": self._extract_field(
                text,
                r"Consumer Number\s+(.+)",
            ),
            "meter_number": self._extract_field(
                text,
                r"Meter Number\s+(.+)",
            ),
            "billing_period": (
                self._extract_period(text)
            ),
            "bill_number": self._extract_field(
                text,
                r"Bill Number\s+(.+)",
            ),
            "currency": self._extract_field(
                text,
                r"Currency\s+([A-Z]{3})",
            ),
            "usage": {
                "previous_reading": (
                    self._extract_amount(
                        text,
                        "Previous Meter Reading",
                    )
                ),
                "current_reading": (
                    self._extract_amount(
                        text,
                        "Current Meter Reading",
                    )
                ),
                "units_consumed": (
                    self._extract_amount(
                        text,
                        "Units Consumed",
                    )
                ),
                "rate_per_unit": (
                    self._extract_amount(
                        text,
                        "Rate per Unit",
                    )
                ),
            },
            "charges": {
                "energy_charges": (
                    self._extract_amount(
                        text,
                        "Energy Charges",
                    )
                ),
                "taxes_and_fees": (
                    self._extract_amount(
                        text,
                        "Taxes and Fees",
                    )
                ),
                "total_amount_due": (
                    self._extract_amount(
                        text,
                        "Total Amount Due",
                    )
                ),
            },
            "payment": {
                "due_date": (
                    self._extract_date_field(
                        text,
                        "Due Date",
                    )
                ),
                "status": self._extract_field(
                    text,
                    r"Payment Status\s+(.+)",
                ),
                "payment_amount": (
                    self._extract_amount(
                        text,
                        "Payment Amount",
                    )
                ),
            },
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
    def _extract_amount(
        text: str,
        field_name: str,
    ) -> float | None:

        pattern = (
            re.escape(field_name)
            + r"\s+"
            + r"(-?\d[\d,]*(?:\.\d+)?)"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        try:
            return float(
                Decimal(
                    match.group(1).replace(
                        ",",
                        "",
                    )
                )
            )

        except InvalidOperation:
            return None

    @staticmethod
    def _extract_period(
        text: str,
    ) -> dict[str, str] | None:

        pattern = (
            r"Billing Period\s+"
            r"(\d{2}-[A-Za-z]{3}-\d{4})"
            r"\s+to\s+"
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
            start = datetime.strptime(
                match.group(1),
                "%d-%b-%Y",
            ).date()

            end = datetime.strptime(
                match.group(2),
                "%d-%b-%Y",
            ).date()

        except ValueError:
            return None

        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
        }

    @classmethod
    def _extract_date_field(
        cls,
        text: str,
        field_name: str,
    ) -> str | None:

        pattern = (
            re.escape(field_name)
            + r"\s+"
            + r"(\d{2}-[A-Za-z]{3}-\d{4})"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        try:
            return datetime.strptime(
                match.group(1),
                "%d-%b-%Y",
            ).date().isoformat()

        except ValueError:
            return None