"""
暴雪战网账号管理工具 - 令牌管理模块
负责保存和管理OAuth登录令牌/回调URL
"""
import os
import json
import subprocess
from datetime import datetime
from config import DATA_DIR, ensure_dirs


class TokenManager:
    """OAuth令牌管理类"""
    
    def __init__(self):
        ensure_dirs()
        self.tokens_dir = os.path.join(DATA_DIR, "tokens")
        os.makedirs(self.tokens_dir, exist_ok=True)
    
    def save_token(self, account_id: str, token_data: dict) -> bool:
        """
        保存登录令牌数据
        
        Args:
            account_id: 账号ID
            token_data: 令牌数据，包含callback_url等信息
        
        Returns:
            bool: 是否保存成功
        """
        try:
            token_file = os.path.join(self.tokens_dir, f"{account_id}.json")
            save_data = {
                "account_id": account_id,
                "saved_at": datetime.now().isoformat(),
                **token_data
            }
            
            with open(token_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存令牌失败: {e}")
            return False
    
    def load_token(self, account_id: str) -> dict:
        """加载账号的令牌数据"""
        try:
            token_file = os.path.join(self.tokens_dir, f"{account_id}.json")
            if not os.path.exists(token_file):
                return {}
            
            with open(token_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载令牌失败: {e}")
            return {}
    
    def has_valid_token(self, account_id: str) -> bool:
        """检查账号是否有有效令牌"""
        token = self.load_token(account_id)
        return bool(token.get("callback_url") or token.get("auth_code"))
    
    def trigger_login(self, account_id: str) -> bool:
        """
        使用保存的令牌触发客户端登录
        
        暴雪战网使用自定义协议 battlenet:// 来接收登录回调
        """
        token_data = self.load_token(account_id)
        
        callback_url = token_data.get("callback_url")
        if callback_url:
            try:
                # 使用系统默认方式打开协议URL
                # 这会触发暴雪战网客户端接收登录信息
                if callback_url.startswith("battlenet://"):
                    subprocess.run(["start", "", callback_url], shell=True)
                    return True
                else:
                    # 如果是普通URL，用浏览器打开
                    os.startfile(callback_url)
                    return True
            except Exception as e:
                print(f"触发登录失败: {e}")
                return False
        
        return False
    
    def delete_token(self, account_id: str) -> bool:
        """删除账号的令牌"""
        try:
            token_file = os.path.join(self.tokens_dir, f"{account_id}.json")
            if os.path.exists(token_file):
                os.remove(token_file)
            return True
        except Exception as e:
            print(f"删除令牌失败: {e}")
            return False
    
    def get_token_info(self, account_id: str) -> dict:
        """获取令牌信息（不包含敏感数据）"""
        token_data = self.load_token(account_id)
        if not token_data:
            return {"exists": False}
        
        return {
            "exists": True,
            "saved_at": token_data.get("saved_at", "未知"),
            "has_callback": bool(token_data.get("callback_url")),
            "has_auth_code": bool(token_data.get("auth_code"))
        }
