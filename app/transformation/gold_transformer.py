from typing import Any


class GoldTransformer:
    """Transforms Silver data into business-level insights."""

    def transform(
        self,
        silver_document: dict[str, Any],
    ) -> dict[str, Any]:

        transactions = silver_document.get(
            "transactions",
            [],
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
                transaction.get("description", "")
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

        return {
            "document_type": silver_document.get(
                "document_type"
            ),
            "period": silver_document.get(
                "statement_period"
            ),
            "financial_summary": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "closing_balance": silver_document
                .get("summary", {})
                .get("closing_balance"),
            },
            "expense_categories": {
                "utilities": utility_expenses,
                "groceries": grocery_expenses,
                "shopping": shopping_expenses,
                "credit_card": credit_card_expenses,
                "transfers": transfer_expenses,
            },
        }