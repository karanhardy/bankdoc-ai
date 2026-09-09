from pathlib import Path

import pymupdf


SOURCE_PDF = Path(
    "data/sample_documents/bank_statement_january.pdf"
)

OUTPUT_PDF = Path(
    "data/sample_documents/"
    "bank_statement_january_scanned.pdf"
)


def main() -> None:
    print("Creating scanned PDF...")

    source = pymupdf.open(
        str(SOURCE_PDF)
    )

    output = pymupdf.open()

    try:
        for page_number, page in enumerate(
            source,
            start=1,
        ):
            print(
                f"Rendering page {page_number}..."
            )

            # Render the original page as an image.
            pixmap = page.get_pixmap(
                dpi=200,
                alpha=False,
            )

            # IMPORTANT:
            # PDF page dimensions are points,
            # NOT pixels.
            new_page = output.new_page(
                width=page.rect.width,
                height=page.rect.height,
            )

            # Insert the rendered image so the new
            # PDF contains only image data.
            new_page.insert_image(
                new_page.rect,
                pixmap=pixmap,
            )

    finally:
        source.close()

    output.save(
        str(OUTPUT_PDF)
    )

    output.close()

    print(
        f"\nCreated: {OUTPUT_PDF}"
    )


if __name__ == "__main__":
    main()