import argparse
import os
import tempfile

from mkv_merge.logging import lcb
from mkv_merge.mkvlib import sdk


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
        "--temp-dir",
        type=str,
        help="Temporary directory (default: auto-created)",
    )
    parser.add_argument(
        "--cache",
        type=str,
        help="Font cache file (default: temp-dir/font-cache.json)",
    )
    parser.add_argument(
        "--font-dir",
        type=str,
        default="Fonts",
        help="Font directory (default: Fonts)",
    )
    parser.add_argument("files", nargs="*", help="MKV files or directories")

    args = parser.parse_args()

    # 处理临时目录
    if args.temp_dir is None:
        args.temp_dir = tempfile.mkdtemp()
    else:
        os.makedirs(args.temp_dir, exist_ok=True)

    # 处理缓存文件路径
    if args.cache is None:
        args.cache = os.path.join(args.temp_dir, "font-cache.json")

    # 处理字体目录
    os.makedirs(args.font_dir, exist_ok=True)

    # 处理输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 初始化 mkvlib
    sdk.initInstance(lcb)
    sdk.cache(args.cache)
    sdk.nrename(True)
    sdk.createFontsCache(args.font_dir, args.cache, lcb)

    # 打印处理后的参数
    print(f"Output directory: {args.output_dir}")
    print(f"Temporary directory: {args.temp_dir}")
    print(f"Font cache file: {args.cache}")
    print(f"Font directory: {args.font_dir}")
    print(f"MKV files and directories to process: {args.files}")

    # 在这里添加处理文件和目录的逻辑
    for file_or_dir in args.files:
        if os.path.isfile(file_or_dir) and file_or_dir.split(".")[-1] == "mkv":
            print(f"Processing file: {file_or_dir}")
        elif os.path.isdir(file_or_dir):
            print(f"Processing directory: {file_or_dir}")
        else:
            print(f"Invalid path: {file_or_dir}")


if __name__ == "__main__":
    main()
