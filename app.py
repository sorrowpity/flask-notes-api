from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from models import db, Note, User
from datetime import datetime, timedelta
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from passlib.context import CryptContext
import os

app = Flask(__name__)
app.secret_key = "my-super-secret-key-2026"

# ===================== 自动三环境适配 =====================
import socket

# 自动判断环境
def get_db_uri():
    # 本地 Windows 开发
    if os.name == "nt":
        return "sqlite:///notes.db"
    # Linux 服务器（阿里云/虚拟机）
    else:
        return "mysql+pymysql://noteuser:123456@localhost:3306/note_db"

DB_URI = get_db_uri()

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.config['JWT_SECRET_KEY'] = 'my-super-secret-key-2026'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# 初始化插件
db.init_app(app)
jwt = JWTManager(app)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 创建表
with app.app_context():
    db.create_all()
    
    # ===================== 自动创建 root 管理员 =====================
    root_user = User.query.filter_by(username="root").first()
    if not root_user:
        root_password = pwd_context.hash("123456")  # 默认密码：123456
        new_root = User(username="root", password=root_password)
        db.session.add(new_root)
        db.session.commit()
        print("✅ 超级管理员 root 已创建，密码：123456")

# ===================== 工具函数 =====================
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

def login_required():
    if not get_current_user():
        return redirect("/login")
    return None

# ===================== 页面路由 =====================
@app.route('/')
def index():
    check = login_required()
    if check: return check
    user = get_current_user()
    notes = Note.query.filter_by(user_id=user.id).order_by(Note.update_time.desc()).all()
    return render_template('index.html', notes=notes, username=user.username)

@app.route('/add', methods=['GET', 'POST'])
def add_note():
    check = login_required()
    if check: return check
    user = get_current_user()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            return "标题和内容不能为空！<a href='/add'>返回</a>"
        note = Note(title=title, content=content, user_id=user.id)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_note.html')

@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    check = login_required()
    if check: return check
    user = get_current_user()
    note = Note.query.filter_by(id=note_id, user_id=user.id).first_or_404()
    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit_note.html', note=note)

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    check = login_required()
    if check: return check
    user = get_current_user()
    note = Note.query.filter_by(id=note_id, user_id=user.id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/search')
def search_note():
    check = login_required()
    if check: return check
    user = get_current_user()
    keyword = request.args.get('keyword', '').strip()
    if keyword:
        notes = Note.query.filter(
            Note.user_id == user.id,
            Note.title.like(f'%{keyword}%')
        ).order_by(Note.update_time.desc()).all()
    else:
        notes = Note.query.filter_by(user_id=user.id).order_by(Note.update_time.desc()).all()
    return render_template('index.html', notes=notes)

# ===================== 登录、注册页面 =====================
@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ===================== 接口（保留你原来的） =====================
def success_response(data=None, message="操作成功"):
    return jsonify({"code":200,"message":message,"data":data,"timestamp":datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

def error_response(code=400, message="操作失败", data=None):
    return jsonify({"code":code,"message":message,"data":data}), code

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username","").strip()
    password = data.get("password","").strip()
    if not username or not password:
        return error_response(400,"用户名和密码不能为空")
    if User.query.filter_by(username=username).first():
        return error_response(400,"用户名已存在")
    user = User(username=username, password=pwd_context.hash(password))
    db.session.add(user)
    db.session.commit()
    return success_response(message="注册成功")

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username","").strip()
    password = data.get("password","").strip()
    user = User.query.filter_by(username=username).first()
    if not user or not pwd_context.verify(password, user.password):
        return error_response(400,"用户名或密码错误")
    session["user_id"] = user.id
    return success_response(data={"token":create_access_token(identity=str(user.id))}, message="登录成功")

# -------------------------- API 接口 --------------------------
@app.route('/api/notes', methods=['GET'])
@jwt_required()
def get_notes_api():
    user_id = int(get_jwt_identity())
    notes = Note.query.filter_by(user_id=user_id).order_by(Note.update_time.desc()).all()
    return success_response(data=Note.to_dict_list(notes))

@app.route('/api/notes', methods=['POST'])
@jwt_required()
def add_note_api():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = data.get('title','').strip()
    content = data.get('content','').strip()
    if not title or not content:
        return error_response(400,"标题和内容不能为空")
    note = Note(title=title, content=content, user_id=user_id)
    db.session.add(note)
    db.session.commit()
    return success_response(data=note.to_dict()), 201

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note_api(note_id):
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return error_response(404,"笔记不存在")
    db.session.delete(note)
    db.session.commit()
    return success_response()

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note_api(note_id):
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return error_response(404,"笔记不存在")
    data = request.get_json() or {}
    title = data.get('title','').strip()
    content = data.get('content','').strip()
    if not title or not content:
        return error_response(400,"标题和内容不能为空")
    note.title = title
    note.content = content
    db.session.commit()
    return success_response(data=note.to_dict())

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)