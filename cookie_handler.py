"""
暴雪战网账号管理工具 - Cookie处理模块
负责保存、加载和管理浏览器Cookie
"""
import os
import json
import pickle
from datetime import datetime
from config import COOKIES_DIR, ensure_dirs


class CookieHandler:
    """Cookie处理类"""
    
    def __init__(self):
        ensure_dirs()
    
    def save_cookies(self, account_id: str, cookies: list, driver=None) -> bool:
        """
        保存cookies到文件
        
        Args:
            account_id: 账号ID
            cookies: cookie列表
            driver: selenium webdriver实例（可选，用于直接获取cookies）
        
        Returns:
            bool: 是否保存成功
        """
        try:
            if driver:
                cookies = driver.get_cookies()
            
            cookie_file = os.path.join(COOKIES_DIR, f"{account_id}.json")
            cookie_data = {
                "account_id": account_id,
                "cookies": cookies,
                "saved_at": datetime.now().isoformat(),
                "cookie_count": len(cookies)
            }
            
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存Cookie失败: {e}")
            return False
    
    def load_cookies(self, account_id: str) -> list:
        """
        从文件加载cookies
        
        Args:
            account_id: 账号ID
        
        Returns:
            list: cookie列表，失败返回空列表
        """
        try:
            cookie_file = os.path.join(COOKIES_DIR, f"{account_id}.json")
            if not os.path.exists(cookie_file):
                return []
            
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            return cookie_data.get("cookies", [])
        except Exception as e:
            print(f"加载Cookie失败: {e}")
            return []
    
    def apply_cookies(self, driver, account_id: str) -> bool:
        """
        将保存的cookies应用到浏览器
        
        Args:
            driver: selenium webdriver实例
            account_id: 账号ID
        
        Returns:
            bool: 是否应用成功
        """
        try:
            cookies = self.load_cookies(account_id)
            if not cookies:
                return False
            
            # 先删除现有cookies
            driver.delete_all_cookies()
            
            # 添加保存的cookies
            for cookie in cookies:
                # 处理可能的兼容性问题
                try:
                    # 移除可能导致问题的字段
                    cookie_clean = {k: v for k, v in cookie.items() 
                                   if k in ['name', 'value', 'domain', 'path', 'secure', 'httpOnly', 'expiry']}
                    driver.add_cookie(cookie_clean)
                except Exception as cookie_error:
                    print(f"添加单个cookie失败: {cookie_error}")
                    continue
            
            return True
        except Exception as e:
            print(f"应用Cookie失败: {e}")
            return False
    
    def delete_cookies(self, account_id: str) -> bool:
        """
        删除账号的cookies文件
        
        Args:
            account_id: 账号ID
        
        Returns:
            bool: 是否删除成功
        """
        try:
            cookie_file = os.path.join(COOKIES_DIR, f"{account_id}.json")
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
            return True
        except Exception as e:
            print(f"删除Cookie失败: {e}")
            return False
    
    def get_cookie_info(self, account_id: str) -> dict:
        """
        获取cookie信息（不包含实际cookie值）
        
        Args:
            account_id: 账号ID
        
        Returns:
            dict: cookie信息
        """
        try:
            cookie_file = os.path.join(COOKIES_DIR, f"{account_id}.json")
            if not os.path.exists(cookie_file):
                return {"exists": False}
            
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            return {
                "exists": True,
                "saved_at": cookie_data.get("saved_at", "未知"),
                "cookie_count": cookie_data.get("cookie_count", 0)
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}
