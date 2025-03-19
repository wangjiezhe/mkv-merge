#!/root/mkv-merge/.venv/bin/python


import logging
from pathlib import Path
from pprint import pprint

from colorama import Fore, Style, init

from mkv_merge.mkvlib import sdk

# 初始化 colorama
init(autoreset=True)

# 定义日志级别与颜色的映射
LOG_COLORS = {
    logging.INFO: Fore.WHITE,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.DEBUG: Fore.BLUE,
    2: Fore.RED + Style.BRIGHT,  # SWarning
    4: Fore.GREEN,  # Progress
}


# 自定义日志格式化类
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_level = record.levelno
        color = LOG_COLORS.get(log_level, Fore.WHITE)
        message = super().format(record)
        return color + message


# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# 设置自定义的格式化器
formatter = ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# 添加处理器到日志器
logger.addHandler(console_handler)

# 自定义日志级别
SWARNING = 2
PROGRESS = 4
logging.addLevelName(SWARNING, "SWARNING")
logging.addLevelName(PROGRESS, "PROGRESS")


def get_ass_files(mkv_file: str) -> list:
    mkv_path = Path(mkv_file)
    mkv_filename = mkv_path.stem
    directory_path = mkv_path.parent

    ass_files = [
        file
        for file in directory_path.glob("*")
        if file.is_file()
        and file.name.startswith(mkv_filename)
        and file.suffix == ".ass"
    ]

    return [str(file) for file in ass_files]


# 测试文件
mkv_file = "S01E01.mkv"
ass_files = get_ass_files(mkv_file)
font_dir = "Fonts"
sample_font = "A-OTF-Jun501Pro-Bold.otf"
font_cache = "fcache.json"
out_dir = "dist"

sample_font_path = Path(font_dir, sample_font).as_posix()


# 日志回调函数
def lcb(log_level, info):
    match log_level:
        case 0:
            logger.info(info)
        case 1:
            logger.warning(info)
        case 2:
            logger.log(SWARNING, info)
        case 3:
            logger.error(info)
        case 4:
            logger.log(PROGRESS, info)
        case _:
            raise ValueError(f"Strange log level: {log_level}")


# 初始化
sdk.initInstance(lcb)
sdk.cache([font_cache])
sdk.nrename(True)
sdk.createFontsCache(font_dir, font_cache, lcb)


def test():
    print(f"mkvlib 版本: {sdk.version()}", end="\n\n")

    print(f"{sample_font} 的信息:")
    pprint(sdk.getFontInfo(sample_font_path))
    print()

    print(f"{mkv_file} 的信息:")
    pprint(sdk.getMKVInfo(mkv_file))
    print()

    already_subset, failed = sdk.checkSubset(mkv_file, lcb)
    if not failed:
        print(f"{mkv_file} {'不' if already_subset else ''}需要进行字体子集化")
    else:
        raise ValueError(f"查询子集化出错: {mkv_file}")
    print()

    print(f"{ass_files} 中用到的字体:")
    need_fonts, failed_fonts = sdk.getFontsList(ass_files, font_dir, lcb)
    pprint(need_fonts)
    if failed_fonts:
        print("找不到以下字体:")
        pprint(failed_fonts)
    print()

    # res = sdk.copyFontsFromCache(ass_files, out_dir, lcb)
    # if res:
    #     print(f"成功为 {ass_files} 导出所需字体")
    # else:
    #     print("导出字体失败！")

    res = sdk.assFontSubset(ass_files, font_dir, out_dir, True, lcb)
    if res:
        print(f"成功为 {ass_files} 导出子集化字体")
    else:
        print("子集化字体失败！")


if __name__ == "__main__":
    test()
