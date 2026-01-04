"""
暴雪战网账号管理工具 - 浏览器控制模块
监控OAuth登录流程，捕获登录令牌
"""
import os
import time
import subprocess
import winreg
import json
import re
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import BATTLENET_LOGIN_URL, DATA_DIR
from cookie_handler import CookieHandler
from account_manager import AccountManager
from token_manager import TokenManager


class BrowserController:
    """浏览器控制类"""
    
    def __init__(self, browser_type="edge"):
        """
        初始化浏览器控制器
        
        Args:
            browser_type: 浏览器类型 ("edge" 或 "chrome")
        """
        self.browser_type = browser_type
        self.driver = None
        self.cookie_handler = CookieHandler()
        self.account_manager = AccountManager()
        self.token_manager = TokenManager()
        self.captured_callback = None
    
    def _find_edge_driver(self):
        """查找系统中的 Edge 驱动"""
        # 常见的 msedgedriver 位置
        possible_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'Application', 'msedgedriver.exe'),
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Microsoft', 'Edge', 'Application', 'msedgedriver.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Microsoft', 'Edge', 'Application', 'msedgedriver.exe'),
            r'C:\Windows\System32\msedgedriver.exe',
            os.path.join(DATA_DIR, 'msedgedriver.exe'),  # 本地驱动目录
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        return None
    
    def _create_driver(self, headless=False, account_id=None):
        """创建WebDriver实例"""
        # 优先尝试 Edge
        if self._try_create_edge(headless, account_id):
            return True
        
        # 备选尝试 Chrome
        if self._try_create_chrome(headless, account_id):
            return True
        
        return False
    
    def _try_create_edge(self, headless=False, account_id=None):
        """尝试创建 Edge 浏览器"""
        try:
            options = EdgeOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--disable-infobars")
            options.add_argument("--start-maximized")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # 为每个账号创建独立的浏览器配置文件
            if account_id:
                user_data_dir = os.path.join(DATA_DIR, "profiles", f"profile_{account_id}")
            else:
                user_data_dir = os.path.join(DATA_DIR, "browser_profile")
            os.makedirs(user_data_dir, exist_ok=True)
            options.add_argument(f"--user-data-dir={user_data_dir}")
            
            # 方法1：尝试不指定驱动路径，让 Selenium 自动查找
            try:
                self.driver = webdriver.Edge(options=options)
                self._setup_driver()
                return True
            except Exception as e1:
                print(f"Edge 自动查找失败: {e1}")
            
            # 方法2：尝试查找本地驱动
            driver_path = self._find_edge_driver()
            if driver_path:
                try:
                    service = EdgeService(executable_path=driver_path)
                    self.driver = webdriver.Edge(service=service, options=options)
                    self._setup_driver()
                    return True
                except Exception as e2:
                    print(f"使用本地驱动失败: {e2}")
            
            return False
        except Exception as e:
            print(f"创建 Edge 浏览器失败: {e}")
            return False
    
    def _try_create_chrome(self, headless=False, account_id=None):
        """尝试创建 Chrome 浏览器"""
        try:
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--disable-infobars")
            options.add_argument("--start-maximized")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # 为每个账号创建独立的浏览器配置文件
            if account_id:
                user_data_dir = os.path.join(DATA_DIR, "profiles_chrome", f"profile_{account_id}")
            else:
                user_data_dir = os.path.join(DATA_DIR, "browser_profile_chrome")
            os.makedirs(user_data_dir, exist_ok=True)
            options.add_argument(f"--user-data-dir={user_data_dir}")
            
            self.driver = webdriver.Chrome(options=options)
            self._setup_driver()
            self.browser_type = "chrome"
            return True
        except Exception as e:
            print(f"创建 Chrome 浏览器失败: {e}")
            return False
    
    def _setup_driver(self):
        """设置驱动的通用配置"""
        try:
            # 执行JS来隐藏webdriver特征
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            })
        except:
            pass
    
    def open_login_page(self):
        """打开暴雪战网登录页面"""
        if not self.driver:
            if not self._create_driver():
                return False
        
        try:
            self.driver.get(BATTLENET_LOGIN_URL)
            return True
        except Exception as e:
            print(f"打开登录页面失败: {e}")
            return False
    
    def login_with_cookies(self, account_id: str) -> bool:
        """
        使用保存的cookies登录
        
        Args:
            account_id: 账号ID
        
        Returns:
            bool: 是否成功
        """
        if not self.driver:
            if not self._create_driver():
                return False
        
        try:
            # 获取保存的cookies
            cookies = self.cookie_handler.load_cookies(account_id)
            if not cookies:
                print("没有找到保存的Cookie")
                return False
            
            # 按域名分组cookies
            domain_cookies = {}
            for cookie in cookies:
                domain = cookie.get('domain', '')
                if domain not in domain_cookies:
                    domain_cookies[domain] = []
                domain_cookies[domain].append(cookie)
            
            # 首先访问主域名并注入cookies
            self.driver.get("https://account.battlenet.com.cn")
            time.sleep(1)
            
            # 删除现有cookies
            self.driver.delete_all_cookies()
            
            # 注入所有cookies
            for cookie in cookies:
                try:
                    # 清理cookie，只保留必要字段
                    clean_cookie = {}
                    for key in ['name', 'value', 'domain', 'path', 'secure', 'httpOnly']:
                        if key in cookie:
                            clean_cookie[key] = cookie[key]
                    # expiry需要特殊处理
                    if 'expiry' in cookie:
                        clean_cookie['expiry'] = int(cookie['expiry'])
                    
                    self.driver.add_cookie(clean_cookie)
                except Exception as ce:
                    print(f"添加cookie失败 {cookie.get('name')}: {ce}")
                    continue
            
            # 刷新页面使cookies生效
            time.sleep(0.5)
            self.driver.get("https://account.battlenet.com.cn/login")
            time.sleep(2)
            
            # 记录登录
            self.account_manager.record_login(account_id)
            return True
            
        except Exception as e:
            print(f"使用Cookie登录失败: {e}")
            return False
    
    def save_current_cookies(self, account_id: str) -> bool:
        """
        保存当前浏览器的cookies
        
        Args:
            account_id: 账号ID
        
        Returns:
            bool: 是否保存成功
        """
        if not self.driver:
            return False
        
        try:
            return self.cookie_handler.save_cookies(account_id, [], self.driver)
        except Exception as e:
            print(f"保存Cookie失败: {e}")
            return False
    
    def switch_account(self, account_id: str) -> bool:
        """
        切换到指定账号
        
        Args:
            account_id: 目标账号ID
        
        Returns:
            bool: 是否切换成功
        """
        # 检查是否有保存的cookies
        if not self.account_manager.has_valid_cookies(account_id):
            print(f"账号 {account_id} 没有保存的登录状态，需要手动登录")
            return False
        
        return self.login_with_cookies(account_id)
    
    def launch_battlenet_client(self):
        """启动暴雪战网客户端"""
        # 常见的战网安装路径
        possible_paths = [
            r"C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe",
            r"C:\Program Files\Battle.net\Battle.net Launcher.exe",
            r"D:\Battle.net\Battle.net Launcher.exe",
            r"D:\Program Files (x86)\Battle.net\Battle.net Launcher.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen([path])
                    return True
                except Exception as e:
                    print(f"启动战网客户端失败: {e}")
        
        print("未找到战网客户端，请手动启动")
        return False
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def is_logged_in(self) -> bool:
        """检查当前是否已登录"""
        if not self.driver:
            return False
        
        try:
            current_url = self.driver.current_url
            if "login" not in current_url.lower():
                return True
            return False
        except:
            return False
    
    def monitor_oauth_callback(self, account_id: str, timeout: int = 120) -> bool:
        """
        监控OAuth登录流程，捕获登录回调
        
        Args:
            account_id: 账号ID
            timeout: 超时时间（秒）
        
        Returns:
            bool: 是否成功捕获回调
        """
        if not self.driver:
            return False
        
        start_time = time.time()
        captured_data = {}
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                
                # 检查是否有battlenet协议回调
                # 登录成功后可能会触发 battlenet:// 协议
                
                # 检查是否登录成功（重定向到账户页面）
                if "account.battlenet.com.cn" in current_url and "login" not in current_url:
                    # 登录成功，保存cookies和当前状态
                    cookies = self.driver.get_cookies()
                    captured_data["cookies"] = cookies
                    captured_data["final_url"] = current_url
                    captured_data["login_success"] = True
                    
                    # 保存令牌数据
                    self.token_manager.save_token(account_id, captured_data)
                    self.cookie_handler.save_cookies(account_id, cookies)
                    return True
                
                # 检查URL参数中是否有认证码
                if "code=" in current_url or "token=" in current_url:
                    parsed = urlparse(current_url)
                    params = parse_qs(parsed.query)
                    
                    if "code" in params:
                        captured_data["auth_code"] = params["code"][0]
                    if "token" in params:
                        captured_data["token"] = params["token"][0]
                    
                    captured_data["callback_url"] = current_url
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"监控出错: {e}")
                time.sleep(1)
        
        # 超时，但可能已捕获部分数据
        if captured_data:
            self.token_manager.save_token(account_id, captured_data)
            return bool(captured_data.get("login_success"))
        
        return False
    
    def open_login_for_account(self, account_id: str) -> bool:
        """
        为指定账号打开登录页面（使用独立的浏览器配置文件）
        
        Args:
            account_id: 账号ID
        
        Returns:
            bool: 是否成功
        """
        if not self.driver:
            if not self._create_driver(account_id=account_id):
                return False
        
        try:
            # 打开战网登录页面
            self.driver.get(BATTLENET_LOGIN_URL)
            return True
        except Exception as e:
            print(f"打开登录页面失败: {e}")
            return False
    
    def switch_to_account(self, account_id: str) -> bool:
        """
        切换到指定账号 - 使用该账号的浏览器配置文件
        配置文件中保存了之前的登录状态
        
        Args:
            account_id: 账号ID
        
        Returns:
            bool: 是否成功打开
        """
        if not self.driver:
            if not self._create_driver(account_id=account_id):
                return False
        
        try:
            # 打开战网登录页面，浏览器配置文件中的cookies会自动生效
            self.driver.get(BATTLENET_LOGIN_URL)
            return True
        except Exception as e:
            print(f"切换账号失败: {e}")
            return False
    
    def check_profile_exists(self, account_id: str) -> bool:
        """检查账号的浏览器配置文件是否存在"""
        profile_dir = os.path.join(DATA_DIR, "profiles", f"profile_{account_id}")
        return os.path.exists(profile_dir) and os.path.isdir(profile_dir)
