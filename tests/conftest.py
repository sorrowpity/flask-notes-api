import pytest
import os
import sys
from app import app as flask_app
from models import db

# -------------------------
# 真实 Windows 环境测试
# -------------------------
@pytest.fixture(params=["windows", "linux"])  # 关键：自动跑2遍！
def app(request):
    # 保存原始环境，测试完恢复
    original_os_name = os.name
    original_sys_platform = sys.platform

    # 模拟环境
    if request.param == "linux":
        os.name = "posix"
        sys.platform = "linux"
    else:
        os.name = "nt"
        sys.platform = "win32"

    # 测试用内存数据库
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key-123456",
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app  # 测试运行
        db.session.remove()
        db.drop_all()

    # 恢复原始环境
    os.name = original_os_name
    sys.platform = original_sys_platform

# -------------------------
# 客户端固定
# -------------------------
@pytest.fixture
def client(app):
    return app.test_client()

# -------------------------
# JWT 令牌
# -------------------------
@pytest.fixture
def auth_token(app):
    from flask_jwt_extended import create_access_token
    with app.app_context():
        return create_access_token(identity="1")