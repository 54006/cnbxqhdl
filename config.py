"""
暴雪战网账号管理工具 - 配置模块
"""
import os
import sys
import json

def get_app_dir():
    """获取应用目录（支持打包后的exe）"""
    if getattr(sys, 'frozen', False):
        # 打包后的exe，使用exe所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，使用脚本所在目录
        return os.path.dirname(os.path.abspath(__file__))

# 应用目录
APP_DIR = get_app_dir()
DATA_DIR = os.path.join(APP_DIR, "data")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
COOKIES_DIR = os.path.join(DATA_DIR, "cookies")

# 暴雪战网相关URL (网易通行证OAuth)
BATTLENET_LOGIN_URL = "https://account.battlenet.com.cn/login"
NETEASE_LOGIN_URL = "https://oauth.g.mkey.163.com/oauth-front/"

# 确保数据目录存在
def ensure_dirs():
    """确保必要的目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(COOKIES_DIR, exist_ok=True)

# 初始化目录
ensure_dirs()
