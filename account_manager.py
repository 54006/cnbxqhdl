"""
暴雪战网账号管理工具 - 账号管理模块
"""
import os
import json
import uuid
from datetime import datetime
from config import ACCOUNTS_FILE, ensure_dirs
from cookie_handler import CookieHandler


class AccountManager:
    """账号管理类"""
    
    def __init__(self):
        ensure_dirs()
        self.cookie_handler = CookieHandler()
        self.accounts = self._load_accounts()
    
    def _load_accounts(self) -> dict:
        """加载账号列表"""
        try:
            if os.path.exists(ACCOUNTS_FILE):
                with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"加载账号列表失败: {e}")
            return {}
    
    def _save_accounts(self) -> bool:
        """保存账号列表"""
        try:
            with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存账号列表失败: {e}")
            return False
    
    def add_account(self, nickname: str, note: str = "") -> str:
        """
        添加新账号
        
        Args:
            nickname: 账号昵称/备注名
            note: 额外备注
        
        Returns:
            str: 账号ID
        """
        account_id = str(uuid.uuid4())[:8]
        self.accounts[account_id] = {
            "nickname": nickname,
            "note": note,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "login_count": 0
        }
        self._save_accounts()
        return account_id
    
    def remove_account(self, account_id: str) -> bool:
        """
        删除账号
        
        Args:
            account_id: 账号ID
        
        Returns:
            bool: 是否删除成功
        """
        if account_id in self.accounts:
            del self.accounts[account_id]
            self.cookie_handler.delete_cookies(account_id)
            self._save_accounts()
            return True
        return False
    
    def update_account(self, account_id: str, nickname: str = None, note: str = None) -> bool:
        """
        更新账号信息
        
        Args:
            account_id: 账号ID
            nickname: 新昵称
            note: 新备注
        
        Returns:
            bool: 是否更新成功
        """
        if account_id not in self.accounts:
            return False
        
        if nickname is not None:
            self.accounts[account_id]["nickname"] = nickname
        if note is not None:
            self.accounts[account_id]["note"] = note
        
        self._save_accounts()
        return True
    
    def record_login(self, account_id: str):
        """记录登录时间"""
        if account_id in self.accounts:
            self.accounts[account_id]["last_login"] = datetime.now().isoformat()
            self.accounts[account_id]["login_count"] = self.accounts[account_id].get("login_count", 0) + 1
            self._save_accounts()
    
    def get_account(self, account_id: str) -> dict:
        """获取账号信息"""
        account = self.accounts.get(account_id, {}).copy()
        if account:
            account["id"] = account_id
            account["cookie_info"] = self.cookie_handler.get_cookie_info(account_id)
        return account
    
    def get_all_accounts(self) -> list:
        """获取所有账号列表"""
        accounts = []
        for account_id, account_data in self.accounts.items():
            account = account_data.copy()
            account["id"] = account_id
            account["cookie_info"] = self.cookie_handler.get_cookie_info(account_id)
            accounts.append(account)
        return accounts
    
    def has_valid_cookies(self, account_id: str) -> bool:
        """检查账号是否有有效的cookies"""
        cookie_info = self.cookie_handler.get_cookie_info(account_id)
        return cookie_info.get("exists", False)
