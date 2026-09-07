import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class BronzeStorage:
    """Stores raw document extraction results."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        source_file: Path,
        pages: list[dict[str, Any]],
    ) -> Path:
        """
        Save raw extracted document data.

        Bronze should preserve the original extraction
        with minimal transformation.
        """

        source_file = Path(source_file)

        document = {
            "document_id": source_file.stem,
            "source_file": source_file.name,
            "ingestion_timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "pages": pages,
        }

        output_file = (
            self.output_dir
            / f"{source_file.stem}.json"
        )

        with output_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                document,
                file,
                indent=2,
                ensure_ascii=False,
            )

        return output_file