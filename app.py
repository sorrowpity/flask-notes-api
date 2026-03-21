from flask import Flask
from flask_jwt_extended import JWTManager
from models import db
from config import *
from routes import register_routes
from logger import init_logger

# 新增：初始化日志（第一行执行，保证全程日志可用）
logger = init_logger()
app = Flask(__name__)

# 加载配置
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['JSON_AS_ASCII'] = JSON_AS_ASCII
app.config['SECRET_KEY'] = SECRET_KEY
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES

# 初始化插件
db.init_app(app)
jwt = JWTManager(app)

# 注册路由
register_routes(app)

# 创建表 + 自动创建 root
with app.app_context():
    db.create_all()
    from models import User
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    root_user = User.query.filter_by(username="root").first()
    if not root_user:
        root_password = pwd_context.hash("123456")
        new_root = User(username="root", password=root_password)
        db.session.add(new_root)
        db.session.commit()
        print("✅ 超级管理员 root 已创建，密码：123456")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)