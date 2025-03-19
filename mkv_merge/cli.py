import argparse
import os
import sys
import tempfile

from mkv_merge.create import create_mkv
from mkv_merge.logging import lcb
from mkv_merge.mkvlib import sdk


def _create_temp_file(prefix, suffix):
    f, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(f)
    return path


def main():
    parser = argparse.ArgumentParser(description="Merge mkv/mka/ass files")

    # 添加命令行参数
    parser.add_argument(
        "--output-dir",
        type=str,
        default="dist",
        help="Output directory (default: dist)",
    )
    parser.add_argument(
        "--font-dir",
        type=str,
        default="Fonts",
        help="Font directory (default: Fonts)",
    )
    parser.add_argument("files", nargs="*", help="MKV files or directories")

    args = parser.parse_args()

    if not args.files:
        parser.print_help()
        sys.exit(1)

    # 处理缓存文件路径
    font_cache = _create_temp_file("fcache-", ".json")

    # 处理字体目录
    os.makedirs(args.font_dir, exist_ok=True)

    # 处理输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 初始化 mkvlib
    sdk.initInstance(lcb)
    sdk.cache(font_cache)
    sdk.nrename(True)
    sdk.createFontsCache(args.font_dir, font_cache, lcb)

    # 在这里添加处理文件和目录的逻辑
    for file_or_dir in args.files:
        if os.path.isfile(file_or_dir) and file_or_dir.split(".")[-1] == "mkv":
            create_mkv(file_or_dir, args.output_dir, args.font_dir)
        elif os.path.isdir(file_or_dir):
            print(f"Processing directory: {file_or_dir}")
        else:
            raise ValueError(f"Invalid path: {file_or_dir}")


if __name__ == "__main__":
    main()
