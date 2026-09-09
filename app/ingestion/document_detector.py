from dataclasses import dataclass
from enum import Enum


class DocumentType(str, Enum):
    """Supported BankDoc document types."""

    BANK_STATEMENT = "bank_statement"
    ELECTRICITY_BILL = "electricity_bill"
    CREDIT_CARD_STATEMENT = "credit_card_statement"
    LOAN_STATEMENT = "loan_statement"
    INSURANCE_STATEMENT = "insurance_statement"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DetectionResult:
    """Result returned by the document detector."""

    document_type: DocumentType
    confidence: float


class DocumentDetector:
    """
    Detects the document type using document-specific keywords.

    This is intentionally deterministic for now.
    Later, an LLM-based classifier can be added for ambiguous
    documents without changing the rest of the pipeline.
    """

    RULES = {
        DocumentType.BANK_STATEMENT: {
            "account holder": 5,
            "account number": 5,
            "statement period": 4,
            "debit": 3,
            "credit": 3,
            "balance": 3,
            "transaction": 2,
            "bank statement": 6,
        },
        DocumentType.ELECTRICITY_BILL: {
            "electricity bill": 7,
            "consumer number": 5,
            "meter number": 4,
            "units consumed": 4,
            "billing period": 3,
            "amount due": 3,
            "due date": 2,
        },
        DocumentType.CREDIT_CARD_STATEMENT: {
            "credit card statement": 7,
            "card number": 5,
            "minimum amount due": 5,
            "total amount due": 4,
            "credit limit": 4,
            "payment due date": 3,
        },
        DocumentType.LOAN_STATEMENT: {
            "loan statement": 7,
            "loan account": 6,
            "principal outstanding": 5,
            "interest rate": 4,
            "emi": 4,
            "outstanding balance": 4,
        },
        DocumentType.INSURANCE_STATEMENT: {
            "insurance policy": 7,
            "policy number": 6,
            "premium": 4,
            "sum insured": 5,
            "policy period": 4,
            "insurance": 2,
        },
    }

    def detect(self, text: str) -> DetectionResult:
        """
        Detect the most likely document type.

        Raises:
            ValueError: If empty text is supplied.
        """

        if not text or not text.strip():
            raise ValueError(
                "Cannot detect document type from empty text."
            )

        normalized_text = self._normalize_text(text)

        scores: dict[DocumentType, int] = {}

        for document_type, keywords in self.RULES.items():
            score = 0

            for keyword, weight in keywords.items():
                if keyword in normalized_text:
                    score += weight

            scores[document_type] = score

        best_type = max(
            scores,
            key=scores.get,
        )

        best_score = scores[best_type]

        if best_score == 0:
            return DetectionResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
            )

        total_score = sum(scores.values())

        confidence = (
            best_score / total_score
            if total_score
            else 0.0
        )

        return DetectionResult(
            document_type=best_type,
            confidence=round(confidence, 3),
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(
            text.lower().split()
        )