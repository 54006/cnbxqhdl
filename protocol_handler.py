"""
暴雪战网账号管理工具 - 协议处理模块
拦截 battlenet:// 协议回调，保存登录令牌
"""
import os
import sys
import json
import winreg
import subprocess
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from config import DATA_DIR, ensure_dirs


class ProtocolHandler:
    """协议处理类 - 拦截和管理battlenet://协议"""
    
    PROTOCOL_NAME = "battlenet"
    APP_NAME = "BattleNetAccountManager"
    
    def __init__(self):
        ensure_dirs()
        self.callbacks_dir = os.path.join(DATA_DIR, "callbacks")
        os.makedirs(self.callbacks_dir, exist_ok=True)
        self.original_handler = None
    
    def get_current_handler(self):
        """获取当前battlenet://协议的处理程序路径"""
        try:
            key_path = f"SOFTWARE\\Classes\\{self.PROTOCOL_NAME}\\shell\\open\\command"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "")
            winreg.CloseKey(key)
            return value
        except:
            try:
                key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, 
                                    f"{self.PROTOCOL_NAME}\\shell\\open\\command", 0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                return value
            except:
                return None
    
    def save_original_handler(self):
        """保存原始协议处理程序"""
        handler = self.get_current_handler()
        if handler:
            config_file = os.path.join(DATA_DIR, "original_handler.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({"handler": handler, "saved_at": datetime.now().isoformat()}, f)
            self.original_handler = handler
            return True
        return False
    
    def load_original_handler(self):
        """加载原始协议处理程序"""
        config_file = os.path.join(DATA_DIR, "original_handler.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.original_handler = data.get("handler")
                return self.original_handler
        return None
    
    def save_callback(self, account_id: str, callback_url: str) -> bool:
        """
        保存登录回调URL
        
        Args:
            account_id: 账号ID
            callback_url: battlenet:// 回调URL
        
        Returns:
            bool: 是否保存成功
        """
        try:
            callback_file = os.path.join(self.callbacks_dir, f"{account_id}.json")
            
            # 解析URL提取参数
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query) if parsed.query else {}
            
            data = {
                "account_id": account_id,
                "callback_url": callback_url,
                "scheme": parsed.scheme,
                "netloc": parsed.netloc,
                "path": parsed.path,
                "params": {k: v[0] if len(v) == 1 else v for k, v in params.items()},
                "saved_at": datetime.now().isoformat()
            }
            
            with open(callback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存回调失败: {e}")
            return False
    
    def load_callback(self, account_id: str) -> dict:
        """加载账号的回调数据"""
        try:
            callback_file = os.path.join(self.callbacks_dir, f"{account_id}.json")
            if os.path.exists(callback_file):
                with open(callback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"加载回调失败: {e}")
            return {}
    
    def has_callback(self, account_id: str) -> bool:
        """检查是否有保存的回调"""
        callback_file = os.path.join(self.callbacks_dir, f"{account_id}.json")
        return os.path.exists(callback_file)
    
    def trigger_login(self, account_id: str) -> bool:
        """
        使用保存的回调URL触发客户端登录
        
        Args:
            account_id: 账号ID
        
        Returns:
            bool: 是否成功触发
        """
        callback_data = self.load_callback(account_id)
        callback_url = callback_data.get("callback_url")
        
        if not callback_url:
            print(f"账号 {account_id} 没有保存的登录回调")
            return False
        
        try:
            # 使用start命令打开协议URL，这会触发战网客户端
            if callback_url.startswith("battlenet://"):
                # Windows下使用start命令打开协议URL
                subprocess.run(["cmd", "/c", "start", "", callback_url], 
                             shell=False, capture_output=True)
                return True
            else:
                os.startfile(callback_url)
                return True
        except Exception as e:
            print(f"触发登录失败: {e}")
            return False
    
    def delete_callback(self, account_id: str) -> bool:
        """删除账号的回调"""
        try:
            callback_file = os.path.join(self.callbacks_dir, f"{account_id}.json")
            if os.path.exists(callback_file):
                os.remove(callback_file)
            return True
        except:
            return False
    
    def get_callback_info(self, account_id: str) -> dict:
        """获取回调信息摘要"""
        callback_data = self.load_callback(account_id)
        if not callback_data:
            return {"exists": False}
        
        return {
            "exists": True,
            "saved_at": callback_data.get("saved_at", "未知"),
            "has_url": bool(callback_data.get("callback_url"))
        }


def handle_protocol_callback(url: str):
    """
    处理协议回调 - 当程序作为协议处理程序被调用时
    
    Args:
        url: battlenet:// URL
    """
    handler = ProtocolHandler()
    
    # 这里需要确定要保存到哪个账号
    # 暂时保存到一个临时文件，等待用户在GUI中选择
    temp_file = os.path.join(DATA_DIR, "pending_callback.json")
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump({
            "callback_url": url,
            "received_at": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    # 同时转发给原始处理程序（战网客户端）
    original_handler = handler.load_original_handler()
    if original_handler:
        try:
            # 解析原始处理程序命令
            # 通常格式是 "path\to\exe" "%1"
            cmd = original_handler.replace('"%1"', f'"{url}"').replace('%1', url)
            subprocess.Popen(cmd, shell=True)
        except Exception as e:
            print(f"转发给原始处理程序失败: {e}")


if __name__ == "__main__":
    # 当作为协议处理程序被调用时
    if len(sys.argv) > 1:
        url = sys.argv[1]
        if url.startswith("battlenet://"):
            handle_protocol_callback(url)
