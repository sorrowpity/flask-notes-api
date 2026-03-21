import logging
import os
from datetime import datetime

# 自动创建日志目录（三环境都能创建）
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件名：按日期命名，例如 2026-03-21_note_app.log
LOG_FILE = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_note_app.log")

# 配置日志
def init_logger():
    # 日志格式：时间 - 等级 - 文件名:行号 - 内容
    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # 初始化日志器
    logger = logging.getLogger("note_app")
    logger.setLevel(logging.INFO)  # 全局日志等级：INFO/ERROR都记录
    logger.handlers.clear()  # 避免重复打印
    
    # 1. 文件处理器：写入日志文件
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(log_format)
    
    # 2. 控制台处理器：终端/VSCode控制台也能看日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化日志器，项目全局可用
logger = init_logger()