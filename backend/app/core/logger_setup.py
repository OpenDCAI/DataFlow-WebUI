from loguru import logger
import sys

def setup_logging():
    """设置日志配置"""
    # 移除默认的处理器
    logger.remove()
    # 添加一个新的处理器，输出到控制台
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

def get_logger(name=None):
    """获取logger实例，支持指定模块名"""
    # 对于loguru来说，name参数不是必需的，但为了兼容调用方，我们保持接口一致
    return logger


# if __name__ == "__main__":
#     setup_logging()
#     logger = get_logger()
#     logger.info("Logging is set up and ready to go!")
#     logger.warning("This is a warning with colors!")
#     logger.error("This is an error message.")
