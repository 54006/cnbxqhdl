"""
暴雪战网账号切换器 - 独立数据目录方案
每个账号使用完全独立的数据目录，通过符号链接切换
"""
import os
import shutil
import json
import subprocess
import time
import ctypes
import psutil
from datetime import datetime
from config import DATA_DIR, ensure_dirs


def is_admin():
    """检查是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def create_junction(link_path, target_path):
    """创建目录联接（junction point）"""
    # 确保目标路径是绝对路径
    target_path = os.path.abspath(target_path)
    
    # 先删除现有的链接或目录
    if os.path.exists(link_path):
        try:
            # 检查是否是junction
            attrs = ctypes.windll.kernel32.GetFileAttributesW(link_path)
            is_reparse = (attrs != -1) and (attrs & 0x400)
            
            if is_reparse:
                os.rmdir(link_path)
            else:
                shutil.rmtree(link_path, ignore_errors=True)
        except:
            try:
                shutil.rmtree(link_path, ignore_errors=True)
            except:
                pass
        
        time.sleep(0.3)
    
    # 再次确保已删除
    if os.path.exists(link_path):
        try:
            os.rmdir(link_path)
        except:
            try:
                shutil.rmtree(link_path, ignore_errors=True)
            except:
                pass
        time.sleep(0.3)
    
    if os.path.exists(link_path):
        return False
    
    # 使用mklink创建junction
    result = subprocess.run(
        ['cmd', '/c', 'mklink', '/J', link_path, target_path],
        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    return result.returncode == 0 or os.path.exists(link_path)


class IsolatedSwitcher:
    """独立数据目录切换器 - 完全隔离版"""
    
    BATTLENET_EXE = r"C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe"
    BATTLENET_LOCAL = os.path.join(os.environ['LOCALAPPDATA'], 'Battle.net')
    BATTLENET_ROAMING = os.path.join(os.environ['APPDATA'], 'Battle.net')
    
    def __init__(self):
        ensure_dirs()
        self.accounts_dir = os.path.join(DATA_DIR, "isolated_accounts")
        self.accounts_file = os.path.join(DATA_DIR, "isolated_accounts.json")
        self.state_file = os.path.join(DATA_DIR, "switcher_state.json")
        os.makedirs(self.accounts_dir, exist_ok=True)
        self.accounts = self._load_accounts()
        self.current_account_id = self._load_current_account()
    
    def _load_current_account(self) -> str:
        """加载当前活跃的账号ID"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return state.get('current_account_id')
            except:
                pass
        return None
    
    def _save_current_account(self, account_id: str):
        """保存当前活跃的账号ID"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump({'current_account_id': account_id}, f)
    
    def _load_accounts(self) -> dict:
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_accounts(self):
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, ensure_ascii=False, indent=2)
    
    def is_battlenet_running(self) -> bool:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'battle.net' in proc.info['name'].lower():
                    return True
            except:
                pass
        return False
    
    def close_battlenet(self) -> bool:
        closed = False
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] and 'battle.net' in proc.info['name'].lower():
                    proc.terminate()
                    closed = True
            except:
                pass
        if closed:
            time.sleep(3)
        return closed
    
    def start_battlenet(self, region: str = None) -> bool:
        """启动战网，可选指定地区"""
        if os.path.exists(self.BATTLENET_EXE):
            try:
                args = [self.BATTLENET_EXE]
                if region:
                    args.append(f'--setregion={region}')
                subprocess.Popen(args)
                return True
            except:
                pass
        return False
    
    def _cleanup_invalid_junctions(self):
        """清理无效的junction（指向不存在目录的junction）"""
        for path in [self.BATTLENET_LOCAL, self.BATTLENET_ROAMING]:
            # 检查路径是否存在（包括junction）
            if os.path.lexists(path):
                is_junction = self._is_junction(path)
                if is_junction:
                    # 是junction，检查是否有效
                    try:
                        os.listdir(path)
                    except (OSError, PermissionError):
                        # junction无效，用cmd删除
                        subprocess.run(['cmd', '/c', 'rmdir', path], 
                                      capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    
    def get_current_logged_account(self) -> dict:
        """
        自动识别当前登录的战网账号
        从配置文件和日志中提取账号信息
        """
        result = {"account_name": None, "email": None, "battletag": None}
        
        # 先清理无效junction
        self._cleanup_invalid_junctions()
        
        try:
            # 从Battle.net.config读取SavedAccountNames
            config_path = os.path.join(self.BATTLENET_ROAMING, "Battle.net.config")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 获取保存的账号名列表
                saved_names = config.get("Client", {}).get("SavedAccountNames", "")
                if saved_names:
                    # 第一个通常是最近登录的
                    names = [n.strip() for n in saved_names.split(",") if n.strip()]
                    if names:
                        result["email"] = names[0]
                        result["account_name"] = names[0].split("@")[0] if "@" in names[0] else names[0]
            
            # 尝试从日志获取BattleTag
            logs_dir = os.path.join(self.BATTLENET_LOCAL, "Logs")
            if os.path.exists(logs_dir):
                log_files = sorted([f for f in os.listdir(logs_dir) if f.endswith('.log')], reverse=True)
                for log_file in log_files[:3]:  # 检查最近3个日志
                    log_path = os.path.join(logs_dir, log_file)
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # 查找BattleTag
                            import re
                            match = re.search(r'BattleTag[:\s]+([^\s,]+#\d+)', content)
                            if match:
                                result["battletag"] = match.group(1)
                                break
                    except:
                        pass
        except Exception as e:
            print(f"读取账号信息失败: {e}")
        
        return result
    
    def get_account_local_dir(self, account_id: str) -> str:
        """获取账号的LocalAppData目录"""
        return os.path.join(self.accounts_dir, account_id, "LocalAppData")
    
    def get_account_roaming_dir(self, account_id: str) -> str:
        """获取账号的Roaming目录"""
        return os.path.join(self.accounts_dir, account_id, "Roaming")
    
    def create_account(self, nickname: str) -> str:
        """创建新账号（创建空的独立数据目录）"""
        import uuid
        account_id = str(uuid.uuid4())[:8]
        
        local_dir = self.get_account_local_dir(account_id)
        roaming_dir = self.get_account_roaming_dir(account_id)
        
        os.makedirs(local_dir, exist_ok=True)
        os.makedirs(roaming_dir, exist_ok=True)
        
        self.accounts[account_id] = {
            "nickname": nickname,
            "created_time": datetime.now().isoformat(),
            "logged_in": False
        }
        self._save_accounts()
        return account_id
    
    def get_current_junction_target(self) -> str:
        """获取当前junction指向的账号ID"""
        if not self._is_junction(self.BATTLENET_LOCAL):
            return None
        
        # 检查junction指向哪个账号目录
        for acc_id in self.accounts:
            target_dir = self.get_account_local_dir(acc_id)
            if os.path.exists(target_dir):
                # 比较路径
                try:
                    result = subprocess.run(
                        ['cmd', '/c', 'fsutil', 'reparsepoint', 'query', self.BATTLENET_LOCAL],
                        capture_output=True, text=True, encoding='gbk'
                    )
                    if target_dir.lower() in result.stdout.lower():
                        return acc_id
                except:
                    pass
        return None
    
    def prepare_for_new_login(self) -> str:
        """
        准备新账号登录：创建一个干净的临时目录
        返回临时账号ID，用户登录后可以保存
        """
        import uuid
        temp_id = "temp_" + str(uuid.uuid4())[:8]
        
        temp_local = self.get_account_local_dir(temp_id)
        temp_roaming = self.get_account_roaming_dir(temp_id)
        
        # 关闭战网
        if self.is_battlenet_running():
            self.close_battlenet()
            time.sleep(2)
        
        # 创建空目录
        os.makedirs(temp_local, exist_ok=True)
        os.makedirs(temp_roaming, exist_ok=True)
        
        # 删除当前Battle.net目录/junction
        self._remove_dir_or_junction(self.BATTLENET_LOCAL)
        self._remove_dir_or_junction(self.BATTLENET_ROAMING)
        
        # 创建junction指向临时目录
        create_junction(self.BATTLENET_LOCAL, temp_local)
        create_junction(self.BATTLENET_ROAMING, temp_roaming)
        
        # 记录临时状态
        self.current_account_id = temp_id
        self._save_current_account(temp_id)
        
        return temp_id
    
    def save_current_as_account(self, nickname: str) -> str:
        """
        将当前登录状态保存为新账号
        前提：用户已经通过prepare_for_new_login准备并登录
        """
        import uuid
        
        # 检查是否有临时账号
        if not self.current_account_id or not self.current_account_id.startswith("temp_"):
            # 没有临时账号，使用旧的创建方式
            return self.create_account_from_current(nickname)
        
        temp_id = self.current_account_id
        temp_local = self.get_account_local_dir(temp_id)
        temp_roaming = self.get_account_roaming_dir(temp_id)
        
        # 检查临时目录是否有数据
        if not os.path.exists(temp_local) or not os.listdir(temp_local):
            return None
        
        # 生成正式账号ID
        account_id = str(uuid.uuid4())[:8]
        local_dir = self.get_account_local_dir(account_id)
        roaming_dir = self.get_account_roaming_dir(account_id)
        
        try:
            # 关闭战网
            if self.is_battlenet_running():
                self.close_battlenet()
                time.sleep(2)
            
            # 删除junction
            subprocess.run(['cmd', '/c', 'rmdir', self.BATTLENET_LOCAL], capture_output=True)
            subprocess.run(['cmd', '/c', 'rmdir', self.BATTLENET_ROAMING], capture_output=True)
            
            # 重命名临时目录为正式目录
            os.rename(temp_local, local_dir)
            os.rename(temp_roaming, roaming_dir)
            
            # 清理临时目录父文件夹
            temp_parent = os.path.dirname(temp_local)
            if os.path.exists(temp_parent) and not os.listdir(temp_parent):
                os.rmdir(temp_parent)
            
            # 创建junction指向正式目录
            create_junction(self.BATTLENET_LOCAL, local_dir)
            create_junction(self.BATTLENET_ROAMING, roaming_dir)
            
            # 保存账号信息
            self.accounts[account_id] = {
                "nickname": nickname,
                "created_time": datetime.now().isoformat(),
                "logged_in": True
            }
            self._save_accounts()
            
            # 更新当前账号
            self.current_account_id = account_id
            self._save_current_account(account_id)
            
            return account_id
            
        except Exception as e:
            print(f"保存账号失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_account_data(self, account_id: str) -> bool:
        """更新现有账号的数据（用当前登录数据覆盖）"""
        if account_id not in self.accounts:
            return False
        
        local_dir = self.get_account_local_dir(account_id)
        roaming_dir = self.get_account_roaming_dir(account_id)
        
        try:
            # 关闭战网
            if self.is_battlenet_running():
                self.close_battlenet()
                time.sleep(2)
            
            # 断开junction获取当前数据
            self._disconnect_junction()
            
            # 删除旧的账号数据
            if os.path.exists(local_dir):
                shutil.rmtree(local_dir, ignore_errors=True)
            if os.path.exists(roaming_dir):
                shutil.rmtree(roaming_dir, ignore_errors=True)
            
            # 复制当前数据到账号目录
            def ignore_logs(dir, files):
                return ['Logs'] if 'Logs' in files else []
            
            if os.path.exists(self.BATTLENET_LOCAL):
                shutil.copytree(self.BATTLENET_LOCAL, local_dir, ignore=ignore_logs)
            if os.path.exists(self.BATTLENET_ROAMING):
                shutil.copytree(self.BATTLENET_ROAMING, roaming_dir)
            
            # 删除原目录，创建junction
            self._remove_dir_or_junction(self.BATTLENET_LOCAL)
            self._remove_dir_or_junction(self.BATTLENET_ROAMING)
            
            create_junction(self.BATTLENET_LOCAL, local_dir)
            create_junction(self.BATTLENET_ROAMING, roaming_dir)
            
            # 更新当前账号
            self.current_account_id = account_id
            self._save_current_account(account_id)
            
            return True
        except Exception as e:
            print(f"更新账号数据失败: {e}")
            return False
    
    def _disconnect_junction(self):
        """断开junction，将当前数据转为真实目录"""
        # 如果是junction，先获取目标内容，然后断开
        if self._is_junction(self.BATTLENET_LOCAL):
            # 读取junction目标的内容到临时目录
            temp_local = self.BATTLENET_LOCAL + "_temp"
            if os.path.exists(temp_local):
                shutil.rmtree(temp_local)
            # 复制junction目标的内容
            shutil.copytree(self.BATTLENET_LOCAL, temp_local)
            # 删除junction
            subprocess.run(['cmd', '/c', 'rmdir', self.BATTLENET_LOCAL], capture_output=True)
            # 重命名临时目录
            os.rename(temp_local, self.BATTLENET_LOCAL)
        
        if self._is_junction(self.BATTLENET_ROAMING):
            temp_roaming = self.BATTLENET_ROAMING + "_temp"
            if os.path.exists(temp_roaming):
                shutil.rmtree(temp_roaming)
            shutil.copytree(self.BATTLENET_ROAMING, temp_roaming)
            subprocess.run(['cmd', '/c', 'rmdir', self.BATTLENET_ROAMING], capture_output=True)
            os.rename(temp_roaming, self.BATTLENET_ROAMING)
    
    def create_account_from_current(self, nickname: str) -> str:
        """
        从当前登录状态创建新账号
        使用robocopy复制数据，保留登录会话
        """
        import uuid
        account_id = str(uuid.uuid4())[:8]
        
        local_dir = self.get_account_local_dir(account_id)
        roaming_dir = self.get_account_roaming_dir(account_id)
        
        try:
            # 清理无效junction
            self._cleanup_invalid_junctions()
            
            # 清理目标目录
            if os.path.exists(local_dir):
                shutil.rmtree(local_dir, ignore_errors=True)
            if os.path.exists(roaming_dir):
                shutil.rmtree(roaming_dir, ignore_errors=True)
            
            os.makedirs(local_dir, exist_ok=True)
            os.makedirs(roaming_dir, exist_ok=True)
            
            # 复制数据
            subprocess.run(
                ['robocopy', self.BATTLENET_LOCAL, local_dir, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                ['robocopy', self.BATTLENET_ROAMING, roaming_dir, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 保存账号信息
            now = datetime.now().isoformat()
            self.accounts[account_id] = {
                "nickname": nickname,
                "created_time": now,
                "last_login": now,
                "logged_in": True
            }
            self._save_accounts()
            
            # 记录当前活跃账号
            self.current_account_id = account_id
            self._save_current_account(account_id)
            
            return account_id
        except Exception as e:
            print(f"创建账号失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def switch_to_account(self, account_id: str) -> tuple:
        """
        切换到指定账号（使用复制方式，避免数据污染）
        """
        if account_id not in self.accounts:
            return False, "账号不存在"
        
        local_dir = self.get_account_local_dir(account_id)
        roaming_dir = self.get_account_roaming_dir(account_id)
        
        if not os.path.exists(local_dir):
            return False, "账号LocalAppData目录不存在"
        
        if not os.path.exists(roaming_dir):
            return False, "账号Roaming目录不存在"
        
        # 关闭战网
        if self.is_battlenet_running():
            self.close_battlenet()
            time.sleep(3)
        
        try:
            # 删除当前Battle.net目录/junction
            self._remove_dir_or_junction(self.BATTLENET_LOCAL)
            self._remove_dir_or_junction(self.BATTLENET_ROAMING)
            
            time.sleep(0.5)
            
            # 使用robocopy复制账号数据到Battle.net目录
            subprocess.run(
                ['robocopy', local_dir, self.BATTLENET_LOCAL, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                ['robocopy', roaming_dir, self.BATTLENET_ROAMING, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 更新SavedAccountNames，包含所有已保存账号的邮箱
            self._update_saved_account_names(account_id)
            
            # 记录当前活跃账号和切换时间
            self.current_account_id = account_id
            self._save_current_account(account_id)
            
            # 更新最后登录时间
            self.accounts[account_id]['last_login'] = datetime.now().isoformat()
            self._save_accounts()
            
            # 启动战网
            self.start_battlenet()
            
            return True, f"已切换到账号 {self.accounts[account_id]['nickname']}"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"切换失败: {e}"
    
    def _update_saved_account_names(self, current_account_id: str):
        """更新SavedAccountNames，确保包含所有已保存账号的邮箱，当前账号排在第一位"""
        try:
            config_path = os.path.join(self.BATTLENET_ROAMING, "Battle.net.config")
            if not os.path.exists(config_path):
                return
            
            # 收集所有账号的邮箱
            all_emails = []
            # 当前切换的账号邮箱放第一位
            current_email = self.accounts.get(current_account_id, {}).get("email")
            if current_email:
                all_emails.append(current_email)
            
            # 添加其他账号的邮箱
            for acc_id, acc_info in self.accounts.items():
                email = acc_info.get("email")
                if email and email not in all_emails:
                    all_emails.append(email)
            
            if not all_emails:
                return
            
            # 读取并更新配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if "Client" not in config:
                config["Client"] = {}
            
            config["Client"]["SavedAccountNames"] = ",".join(all_emails)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"更新SavedAccountNames失败: {e}")
    
    def _is_junction(self, path: str) -> bool:
        """检查路径是否是junction point"""
        try:
            if not os.path.exists(path):
                return False
            # 使用Windows API检查
            import ctypes
            FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
            if attrs == -1:
                return False
            return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
        except:
            return False
    
    def _remove_dir_or_junction(self, path: str) -> bool:
        """安全删除目录或junction"""
        if not os.path.exists(path):
            return True
        try:
            if self._is_junction(path):
                # junction用rmdir删除
                result = subprocess.run(['cmd', '/c', 'rmdir', path], capture_output=True)
                return result.returncode == 0
            else:
                # 普通目录：先尝试shutil，失败则用PowerShell强制删除
                try:
                    shutil.rmtree(path)
                except:
                    # 使用PowerShell强制删除
                    subprocess.run(
                        ['powershell', '-Command', f'Remove-Item -Path "{path}" -Recurse -Force -ErrorAction SilentlyContinue'],
                        capture_output=True
                    )
                # 确认删除
                if os.path.exists(path):
                    subprocess.run(['cmd', '/c', 'rd', '/s', '/q', path], capture_output=True)
                return not os.path.exists(path)
        except Exception as e:
            print(f"删除目录失败: {path}, 错误: {e}")
            return False
    
    def mark_logged_in(self, account_id: str):
        """标记账号已登录"""
        if account_id in self.accounts:
            self.accounts[account_id]["logged_in"] = True
            self.accounts[account_id]["last_login"] = datetime.now().isoformat()
            self._save_accounts()
    
    def get_all_accounts(self) -> list:
        result = []
        for account_id, info in self.accounts.items():
            local_dir = self.get_account_local_dir(account_id)
            result.append({
                "id": account_id,
                "nickname": info.get("nickname", "未知"),
                "logged_in": info.get("logged_in", False),
                "last_login": info.get("last_login", ""),
                "has_data": os.path.exists(local_dir) and len(os.listdir(local_dir)) > 0
            })
        return result
    
    def delete_account(self, account_id: str) -> bool:
        if account_id in self.accounts:
            del self.accounts[account_id]
            self._save_accounts()
        
        account_dir = os.path.join(self.accounts_dir, account_id)
        if os.path.exists(account_dir):
            shutil.rmtree(account_dir)
        return True


if __name__ == "__main__":
    print(f"管理员权限: {is_admin()}")
    switcher = IsolatedSwitcher()
    print(f"已保存账号: {switcher.get_all_accounts()}")
