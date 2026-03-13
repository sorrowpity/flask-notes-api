# 笔记管理系统API文档
## 基础信息
- 接口前缀：http://127.0.0.1:5000/api
- 数据格式：所有请求/响应均为JSON
- 统一响应格式：
  ```json
  {
      "code": 状态码（200成功/400参数错/404不存在）,
      "message": "提示信息",
      "data": "核心数据（笔记/列表/空）",
      "timestamp": "时间戳"
  }

## 接口列表
### 1.获取所有笔记
- 请求方式：GET
- 接口路径：/notes
- 返回数据示例：
  ```json
  {
      "code": 200,
      "message": "获取笔记成功",
      "data": [
          {"id": 1, "title": "标题1", "content": "内容1"},
          {"id": 2, "title": "标题2", "content": "内容2"}
      ],
      "timestamp": "2023-04-01T08:00:00Z"
  }

### 2.新增笔记
- 请求方式：POST
- 接口路径：/note
- 请求参数（JSON）：
  ```json
  {
      "title": "新标题",
      "content": "新内容"
  }
- 返回数据示例：
  ```json
  {
      "code": 200,
      "message": "添加笔记成功",
      "data": {"id": 3, "title": "新标题", "content": "新内容"},
      "timestamp": "2

### 3.修改笔记
- 请求方式：PUT
- 接口路径：/note/{id}
- 请求参数（JSON）：
  ```json
  {
    "title": "修改后的标题",
    "content": "修改后的内容"
  }
- 返回数据示例：
  ```json
  {
      "code": 200,
      "message": "修改笔记成功",
      "data": {"id": 1, "title": "修改后的标题", "content": "修改后的内容"},
      "timestamp": "2023-04-01T08:00:00Z"
  }

### 4.删除笔记
- 请求方式：DELETE
- 接口路径：/note/{id}
- 返回数据示例：
  ```json
  {
      "code": 200,
      "message": "删除笔记成功",
      "data": null,
      "timestamp": "2023-04-01T08:00:00Z"
  }

