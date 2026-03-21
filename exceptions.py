from flask import jsonify, render_template, request
from logger import logger

# 全局异常捕获
def register_global_exceptions(app):

    # 捕获所有未处理的系统错误（500）
    @app.errorhandler(Exception)
    def global_exception(e):
        # 记录致命错误日志（超级重要！）
        logger.critical(f"【全局异常】路径：{request.path} | 错误：{str(e)}", exc_info=True)

        # 如果是接口 API，返回 JSON
        if request.path.startswith("/api/"):
            return jsonify({
                "code": 500,
                "message": "服务器内部错误",
                "error": str(e)
            }), 500
        # 页面请求，返回友好错误页
        else:
            return render_template("500.html"), 500

    # 404 已经有了，这里统一记录日志
    @app.errorhandler(404)
    def not_found(e):
        logger.warning(f"404 不存在：{request.path}")
        return render_template("404.html"), 404