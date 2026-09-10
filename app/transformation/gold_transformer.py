from typing import Any


class GoldTransformer:
    """
    Transforms Silver documents into business-level Gold data.

    Supported document types:

    - bank_statement
    - electricity_bill

    Each document type has its own transformation strategy,
    but the resulting Gold structure remains consistent.
    """

    def transform(
        self,
        silver_document: dict[str, Any],
    ) -> dict[str, Any]:

        document_type = silver_document.get(
            "document_type"
        )

        if document_type == "bank_statement":
            return self._transform_bank_statement(
                silver_document
            )

        if document_type == "electricity_bill":
            return self._transform_electricity_bill(
                silver_document
            )

        raise ValueError(
            "Unsupported document type for Gold transformation: "
            f"{document_type}"
        )

    # =========================================================
    # BANK STATEMENT
    # =========================================================

    def _transform_bank_statement(
        self,
        silver_document: dict[str, Any],
    ) -> dict[str, Any]:

        transactions = silver_document.get(
            "transactions",
            []
        )

        utility_expenses = 0.0
        grocery_expenses = 0.0
        shopping_expenses = 0.0
        credit_card_expenses = 0.0
        transfer_expenses = 0.0

        total_income = 0.0
        total_expenses = 0.0

        for transaction in transactions:

            debit = transaction.get("debit")
            credit = transaction.get("credit")

            description = (
                transaction.get(
                    "description",
                    ""
                )
                .lower()
            )

            if credit is not None:
                total_income += credit

            if debit is not None:
                total_expenses += debit

                if (
                    "electricity" in description
                    or "internet" in description
                    or "utility" in description
                ):
                    utility_expenses += debit

                elif "grocery" in description:
                    grocery_expenses += debit

                elif "shopping" in description:
                    shopping_expenses += debit

                elif "credit card" in description:
                    credit_card_expenses += debit

                elif (
                    "neft" in description
                    or "transfer" in description
                ):
                    transfer_expenses += debit

        summary = silver_document.get(
            "summary",
            {}
        )

        return {
            "document_type": "bank_statement",

            "period": silver_document.get(
                "statement_period"
            ),

            "financial_summary": {
                "total_income": round(
                    total_income,
                    2,
                ),
                "total_expenses": round(
                    total_expenses,
                    2,
                ),
                "closing_balance": summary.get(
                    "closing_balance"
                ),
            },

            "expense_categories": {
                "utilities": round(
                    utility_expenses,
                    2,
                ),
                "groceries": round(
                    grocery_expenses,
                    2,
                ),
                "shopping": round(
                    shopping_expenses,
                    2,
                ),
                "credit_card": round(
                    credit_card_expenses,
                    2,
                ),
                "transfers": round(
                    transfer_expenses,
                    2,
                ),
            },
        }

    # =========================================================
    # ELECTRICITY BILL
    # =========================================================

    def _transform_electricity_bill(
        self,
        silver_document: dict[str, Any],
    ) -> dict[str, Any]:

        charges = silver_document.get(
            "charges",
            {}
        )

        payment = silver_document.get(
            "payment",
            {}
        )

        total_amount_due = charges.get(
            "total_amount_due"
        )

        if total_amount_due is None:
            total_amount_due = 0.0

        payment_amount = payment.get(
            "payment_amount"
        )

        if payment_amount is None:
            payment_amount = total_amount_due

        return {
            "document_type": "electricity_bill",

            "period": silver_document.get(
                "billing_period"
            ),

            "customer": {
                "name": silver_document.get(
                    "customer_name"
                ),
                "consumer_number": silver_document.get(
                    "consumer_number"
                ),
                "meter_number": silver_document.get(
                    "meter_number"
                ),
            },

            "usage": silver_document.get(
                "usage",
                {}
            ),

            "financial_summary": {
                "total_amount_due": round(
                    total_amount_due,
                    2,
                ),
                "amount_paid": round(
                    payment_amount,
                    2,
                ),
                "payment_status": payment.get(
                    "status"
                ),
            },

            "expense_categories": {
                "utilities": round(
                    total_amount_due,
                    2,
                ),
            },

            "charges": {
                "energy_charges": charges.get(
                    "energy_charges"
                ),
                "taxes_and_fees": charges.get(
                    "taxes_and_fees"
                ),
            },

            "payment": {
                "due_date": payment.get(
                    "due_date"
                ),
                "status": payment.get(
                    "status"
                ),
            },
        }