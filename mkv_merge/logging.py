import logging

from colorama import Fore, Style, init

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
