import json
from pathlib import Path
from typing import Any


class SilverStorage:
    """Stores cleaned and structured documents."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        source_file: Path,
        parsed_document: dict[str, Any],
    ) -> Path:
        """Save structured document data."""

        source_file = Path(source_file)

        output_file = (
            self.output_dir
            / f"{source_file.stem}.json"
        )

        with output_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                parsed_document,
                file,
                indent=2,
                ensure_ascii=False,
            )

        return output_file