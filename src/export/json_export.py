import json
from pathlib import Path

from models import PipelineRecord


def export_json(records: list[PipelineRecord], output_path: Path) -> None:
    data = [r.model_dump(mode="json") for r in records]
    output_path.write_text(json.dumps(data, indent=2))
