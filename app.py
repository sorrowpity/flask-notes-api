from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, Note
from datetime import datetime

# 初始化Flask应用
app = Flask(__name__)

# 配置数据库（SQLite，无需额外安装）
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://noteuser:123456@192.168.159.128:3306/note_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭不必要的警告
app.config['JSON_AS_ASCII'] = False  # 解决中文JSON乱码

# 初始化数据库
db.init_app(app)

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


# -------------------------- 新增：RESTful API接口 --------------------------
# 接口1：获取所有笔记（GET请求）
@app.route('/api/notes', methods=['GET'])
def get_notes_api():
    # 1. 查数据库（和你首页的查询逻辑一样）
    notes = Note.query.order_by(Note.update_time.desc()).all()
    # 2. 转成字典列表（用刚才新增的to_dict_list方法）
    notes_data = Note.to_dict_list(notes)
    # 3. 用统一成功响应返回
    return success_response(data=notes_data, message="获取笔记列表成功")

# 接口2：新增笔记（POST请求，API版）
@app.route('/api/notes', methods=['POST'])
def add_note_api():
    # 1. 接收前端传的JSON数据（不是表单数据！）
    # 你原来的/add是接收表单，API接收JSON，这是核心区别
    data = request.get_json() or {}  # 如果没传数据，返回空字典
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    # 2. 数据校验（和你原来的逻辑一样）
    if not title or not content:
        return error_response(code=400, message="标题和内容不能为空")
    
    # 3. 新增笔记（和你原来的逻辑一样）
    new_note = Note(title=title, content=content)
    db.session.add(new_note)
    db.session.commit()
    
    # 4. 返回新增的笔记数据
    return success_response(data=new_note.to_dict(), message="新增笔记成功"), 201  # 201表示创建成功

# 接口3：删除笔记（DELETE请求，API版）
@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note_api(note_id):
    # 1. 查笔记（和你原来的删除逻辑一样）
    note = Note.query.get(note_id)
    if not note:
        return error_response(code=404, message="笔记不存在")
    
    # 2. 删除笔记
    db.session.delete(note)
    db.session.commit()
    
    # 3. 返回成功（无数据）
    return success_response(data=None, message="删除笔记成功")

# 接口4：修改笔记（PUT请求，API版）
@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note_api(note_id):
    # 1. 先查要修改的笔记是否存在
    note = Note.query.get(note_id)
    if not note:
        return error_response(code=404, message="笔记不存在")
    
    # 2. 接收JSON数据（和新增逻辑一致）
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    # 3. 数据校验
    if not title or not content:
        return error_response(code=400, message="标题和内容不能为空")
    
    # 4. 更新笔记
    note.title = title
    note.content = content
    db.session.commit()
    
    # 5. 返回更新后的笔记数据
    return success_response(data=note.to_dict(), message="修改笔记成功")




@app.errorhandler(404)  # 捕获404错误
def page_not_found(e):
    # 渲染404模板，返回404状态码
    return render_template('404.html'), 404



# ------------------- 运行程序 -------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
