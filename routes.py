from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Note, User
from utils import login_required, get_current_user
from passlib.context import CryptContext
from logger import logger

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ===================== 响应工具 =====================
def success_response(data=None, message="操作成功"):
    return jsonify({"code":200,"message":message,"data":data,"timestamp":datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

def error_response(code=400, message="操作失败", data=None):
    return jsonify({"code":code,"message":message,"data":data}), code

# ===================== 页面路由 =====================
def register_routes(app):

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
                logger.error(f"用户{user.id}（{user.username}）添加笔记失败：标题/内容为空")
                return "标题和内容不能为空！<a href='/add'>返回</a>"
            note = Note(title=title, content=content, user_id=user.id)
            db.session.add(note)
            db.session.commit()
            logger.info(f"用户{user.id}（{user.username}）通过网页添加笔记成功：笔记ID{note.id}，标题{title}")
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
            logger.info(f"用户{user.id}（{user.username}）通过网页编辑笔记成功：笔记ID{note.id}，标题{note.title}")
            return redirect(url_for('index'))
        return render_template('edit_note.html', note=note)

    @app.route('/delete/<int:note_id>', methods=['POST'])
    def delete_note(note_id):
        check = login_required()
        if check: return check
        user = get_current_user()
        note = Note.query.filter_by(id=note_id, user_id=user.id).first_or_404()
        # ========== 新增日志 ==========
        logger.info(f"用户{user.id}（{user.username}）通过网页删除笔记成功：笔记ID{note.id}，标题{note.title}")
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

    @app.route("/api/register", methods=["POST"])
    def register():
        data = request.get_json() or {}
        username = data.get("username","").strip()
        password = data.get("password","").strip()
        if not username or not password:
            logger.error(f"用户注册失败：用户名/密码为空，请求数据：{data}")  # 新增错误日志
            return error_response(400,"用户名和密码不能为空")
        if User.query.filter_by(username=username).first():
            logger.error(f"用户注册失败：用户名{username}已存在")  # 新增错误日志
            return error_response(400,"用户名已存在")
        user = User(username=username, password=pwd_context.hash(password))
        db.session.add(user)
        db.session.commit()
        logger.info(f"用户注册成功：用户名{username}")  # 新增信息日志
        return success_response(message="注册成功")

    @app.route("/api/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        username = data.get("username","").strip()
        password = data.get("password","").strip()
        user = User.query.filter_by(username=username).first()
        if not user or not pwd_context.verify(password, user.password):
            logger.error(f"用户登录失败：用户名{username}，密码错误/用户不存在")  # 新增错误日志
            return error_response(400,"用户名或密码错误")
        session["user_id"] = user.id
        from flask_jwt_extended import create_access_token
        logger.info(f"用户登录成功：用户名{username}，用户ID{user.id}")  # 新增信息日志
        return success_response(data={"token":create_access_token(identity=str(user.id))}, message="登录成功")

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
            logger.error(f"用户{user_id}添加笔记失败：标题/内容为空")  # 新增错误日志
            return error_response(400,"标题和内容不能为空")
        note = Note(title=title, content=content, user_id=user_id)
        db.session.add(note)
        db.session.commit()
        logger.info(f"用户{user_id}添加笔记成功：笔记ID{note.id}，标题{title}")  # 新增信息日志
        return success_response(data=note.to_dict()), 201

    @app.route('/api/notes/<int:note_id>', methods=['DELETE'])
    @jwt_required()
    def delete_note_api(note_id):
        user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
        if not note:
            logger.error(f"用户{user_id}删除笔记失败：笔记ID{note_id}不存在")  # 新增错误日志
            return error_response(404,"笔记不存在")
        db.session.delete(note)
        db.session.commit()
        logger.info(f"用户{user_id}删除笔记成功：笔记ID{note_id}")  # 新增信息日志
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
        logger.warning(f"404错误：访问不存在的路径，请求路径{request.path}，请求方法{request.method}")  # 新增警告日志
        return render_template('404.html'), 404