import os
from pathlib import Path

from mkv_merge.create import create_mkv


def process_mkvs(source_dir: str, output_dir: str, font_dir: str):
    source_path = Path(source_dir)
    source_name = source_path.name
    output_path = Path(output_dir, source_name)
    for mkv_path in source_path.rglob("*.mkv"):
        mkv_output_path = Path(output_path, mkv_path.relative_to(source_path)).parent
        os.makedirs(mkv_output_path, exist_ok=True)
        create_mkv(mkv_path.as_posix(), mkv_output_path.as_posix(), font_dir)
