"""开发启动入口：禁用热重载器，适合脚本/后台启动（避免重载器多进程问题）"""
from run import app

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )
