from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT_DIR = Path("data/sample_documents")


def create_bank_statement() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / "bank_statement_january.pdf"

    document = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "<b>EVEREST NATIONAL BANK</b>",
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            "Monthly Bank Statement",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 10))

    customer_data = [
        ["Account Holder", "Alex Morgan"],
        ["Account Number", "XXXX-XXXX-4582"],
        ["Account Type", "Savings"],
        ["Statement Period", "01-Jan-2026 to 31-Jan-2026"],
        ["Currency", "INR"],
    ]

    customer_table = Table(
        customer_data,
        colWidths=[45 * mm, 110 * mm],
    )

    customer_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(customer_table)
    story.append(Spacer(1, 15))

    transactions = [
        [
            "Date",
            "Description",
            "Debit",
            "Credit",
            "Balance",
        ],
        [
            "02-Jan-2026",
            "Salary Credit",
            "-",
            "85,000.00",
            "125,000.00",
        ],
        [
            "04-Jan-2026",
            "Electricity Bill",
            "2,450.50",
            "-",
            "122,549.50",
        ],
        [
            "06-Jan-2026",
            "Internet Bill",
            "1,199.00",
            "-",
            "121,350.50",
        ],
        [
            "10-Jan-2026",
            "Grocery Store",
            "5,750.00",
            "-",
            "115,600.50",
        ],
        [
            "15-Jan-2026",
            "NEFT Transfer",
            "25,000.00",
            "-",
            "90,600.50",
        ],
        [
            "20-Jan-2026",
            "Credit Card Payment",
            "12,500.00",
            "-",
            "78,100.50",
        ],
        [
            "25-Jan-2026",
            "Online Shopping",
            "8,450.00",
            "-",
            "69,650.50",
        ],
    ]

    transaction_table = Table(
        transactions,
        repeatRows=1,
        colWidths=[
            25 * mm,
            50 * mm,
            25 * mm,
            25 * mm,
            30 * mm,
        ],
    )

    transaction_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "ALIGN",
                    (2, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(transaction_table)

    story.append(Spacer(1, 15))

    summary = [
        ["Opening Balance", "40,000.00"],
        ["Total Credits", "85,000.00"],
        ["Total Debits", "55,349.50"],
        ["Closing Balance", "69,650.50"],
    ]

    summary_table = Table(
        summary,
        colWidths=[70 * mm, 60 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(summary_table)

    document.build(story)

    print(f"Created: {output_file}")


if __name__ == "__main__":
    create_bank_statement()