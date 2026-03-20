from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, Note, User
from datetime import datetime
from datetime import timedelta

# ===================== JWT 登录相关导入 =====================
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from passlib.context import CryptContext

# 初始化Flask应用
app = Flask(__name__)
import os

# ===================== 自动三环境适配 =====================
# 本地Windows开发  → SQLite（无需数据库）
# 虚拟机Docker     → 192.168.159.128
# 云服务器Docker   → host.docker.internal
# ==========================================================
if os.path.exists('/.dockerenv'):
    # 在 Docker 容器内部
    with open('/etc/hostname', 'r') as f:
        container_id = f.read().strip()

    # 判断是云服务器 还是 本地虚拟机
    if 'aliyun' in container_id or 'iZ' in os.uname().nodename:
        # 云服务器 Docker
        DB_URI = "mysql+pymysql://noteuser:123456@host.docker.internal:3306/note_db"
    else:
        # 本地虚拟机 Docker
        DB_URI = "mysql+pymysql://noteuser:123456@192.168.159.128:3306/note_db"
else:
    # 本地 Windows VS Code 开发（无数据库依赖）
    DB_URI = "sqlite:///notes.db"

# 应用配置
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭不必要的警告
app.config['JSON_AS_ASCII'] = False  # 解决中文JSON乱码

# ===================== JWT 配置 =====================
app.config['JWT_SECRET_KEY'] = 'my-super-secret-key-2026'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# 初始化插件
db.init_app(app)
jwt = JWTManager(app)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 创建数据库表（首次运行时执行）
with app.app_context():
    db.create_all()


# -------------------------- 统一响应格式（核心） --------------------------
def success_response(data=None, message="操作成功"):
    """成功响应"""
    return jsonify({
        'code': 200,
        'message': message,
        'data': data,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def error_response(code=400, message="操作失败", data=None):
    """错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }), code

# ===================== 1. 用户注册接口（新增） =====================
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return error_response(400, "用户名和密码不能为空")

    if User.query.filter_by(username=username).first():
        return error_response(400, "用户名已存在")

    hash_pwd = pwd_context.hash(password)
    user = User(username=username, password=hash_pwd)

    db.session.add(user)
    db.session.commit()
    return success_response(message="注册成功")

# ===================== 2. 用户登录接口（新增） =====================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user = User.query.filter_by(username=username).first()
    if not user or not pwd_context.verify(password, user.password):
        return error_response(400, "用户名或密码错误")

    token = create_access_token(identity=str(user.id))
    return success_response(data={"token": token}, message="登录成功")

# ------------------- 核心路由 -------------------
# 1. 首页：笔记列表（GET请求）
@app.route('/', endpoint='home')
def index():
    # 查询所有笔记，按更新时间倒序排列
    notes = Note.query.order_by(Note.update_time.desc()).all()
    return render_template('index.html', notes=notes, username='张津铭')

# 2. 新增笔记：GET（显示表单）+ POST（提交数据）
@app.route('/add', methods=['GET', 'POST'])
def add_note():
    if request.method == 'POST':
        # 接收表单数据（表单的name属性值）
        title = request.form.get('title')
        content = request.form.get('content')
        
        # 简单校验
        if not title or not content:
            return "标题和内容不能为空！<a href='/add'>返回</a>"
        
        # 创建新笔记并保存到数据库
        new_note = Note(title=title, content=content)
        db.session.add(new_note)
        db.session.commit()
        
        # 跳转回首页
        return redirect(url_for('home'))
    
    # GET请求：显示新增表单
    return render_template('add_note.html')

# 3. 编辑笔记：GET（显示表单）+ POST（提交修改）
@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    # 根据ID查询笔记，不存在则返回404
    note = Note.query.get_or_404(note_id)
    
    if request.method == 'POST':
        # 更新笔记内容
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        
        # 校验
        if not note.title or not note.content:
            return "标题和内容不能为空！<a href='/edit/{}'>返回</a>".format(note_id)
        
        # 保存修改
        db.session.commit()
        return redirect(url_for('home'))
    
    # GET请求：显示编辑表单（传递笔记数据）
    return render_template('edit_note.html', note=note)

# 4. 删除笔记（GET请求，简单实现）
@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html', name='张津铭', project='Flask笔记管理系统')

@app.route('/api/note/<int:note_id>')
def get_note_detail(note_id):
    note = Note.query.get_or_404(note_id)
    # 调用to_dict()转字典，返回JSON
    return jsonify(note.to_dict())

@app.route('/search')
def search_note():
    # 获取搜索关键词（GET请求用request.args.get()）
    keyword = request.args.get('keyword', '').strip()
    
    if keyword:
        # 按标题模糊查询（包含关键词）
        # filter(Note.title.like(f'%{keyword}%'))：模糊查询，%是通配符
        notes = Note.query.filter(Note.title.like(f'%{keyword}%')).order_by(Note.update_time.desc()).all()
    else:
        # 无关键词，返回所有笔记
        notes = Note.query.order_by(Note.update_time.desc()).all()
    
    # 渲染首页模板，传入筛选后的notes
    return render_template('index.html', notes=notes)

# -------------------------- RESTful API接口（已加登录验证） --------------------------
# 接口1：获取所有笔记
@app.route('/api/notes', methods=['GET'])
@jwt_required()  # 必须登录
def get_notes_api():
    notes = Note.query.order_by(Note.update_time.desc()).all()
    notes_data = Note.to_dict_list(notes)
    return success_response(data=notes_data, message="获取笔记列表成功")

# 接口2：新增笔记
@app.route('/api/notes', methods=['POST'])
@jwt_required()  # 必须登录
def add_note_api():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return error_response(code=400, message="标题和内容不能为空")
    
    new_note = Note(title=title, content=content)
    db.session.add(new_note)
    db.session.commit()
    
    return success_response(data=new_note.to_dict(), message="新增笔记成功"), 201

# 接口3：删除笔记
@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()  # 必须登录
def delete_note_api(note_id):
    note = Note.query.get(note_id)
    if not note:
        return error_response(code=404, message="笔记不存在")
    
    db.session.delete(note)
    db.session.commit()
    return success_response(data=None, message="删除笔记成功")

# 接口4：修改笔记
@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@jwt_required()  # 必须登录
def update_note_api(note_id):
    note = Note.query.get(note_id)
    if not note:
        return error_response(code=404, message="笔记不存在")
    
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return error_response(code=400, message="标题和内容不能为空")
    
    note.title = title
    note.content = content
    db.session.commit()
    return success_response(data=note.to_dict(), message="修改笔记成功")

@app.errorhandler(404)  # 捕获404错误
def page_not_found(e):
    return render_template('404.html'), 404

# ------------------- 运行程序 -------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)