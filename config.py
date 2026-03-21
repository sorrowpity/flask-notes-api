import os
from datetime import timedelta

# ===================== 自动三环境适配 =====================
def get_db_uri():
    # 本地 Windows 开发
    if os.name == "nt":
        return "sqlite:///notes.db"
    # Linux 服务器（阿里云/虚拟机）
    else:
        return "mysql+pymysql://noteuser:123456@localhost:3306/note_db"

DB_URI = get_db_uri()

# 配置项
SECRET_KEY = "my-super-secret-key-2026"
JWT_SECRET_KEY = "my-super-secret-key-2026"
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
SQLALCHEMY_TRACK_MODIFICATIONS = False
JSON_AS_ASCII = False