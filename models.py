# models.py - 定义数据库模型
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 初始化SQLAlchemy
db = SQLAlchemy()

# ===================== 用户模型 =====================
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    # 关联：一个用户有多条笔记
    notes = db.relationship('Note', backref='user', lazy=True)

# 笔记模型（覆盖数据库CRUD核心）
class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)  # 主键ID
    title = db.Column(db.String(100), nullable=False)  # 笔记标题（必填）
    content = db.Column(db.Text, nullable=False)  # 笔记内容（必填）
    create_time = db.Column(db.DateTime, default=datetime.now)  # 创建时间（自动生成）
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间

    # ===================== 多用户外键（只加这一行） =====================
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 转字典（方便接口返回，也能用于模板渲染）
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M'),
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M')
        }
        
    @staticmethod
    def to_dict_list(notes):
        """笔记列表批量转字典（新增）"""
        return [note.to_dict() for note in notes]