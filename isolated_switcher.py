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
    """独立数据目录切换器 - 完全隔离版，支持国服和国际服"""
    
    # Battle.net路径（国服和国际服共用同一个目录，只是启动参数不同）
    BATTLENET_EXE = r"C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe"
    BATTLENET_LOCAL = os.path.join(os.environ['LOCALAPPDATA'], 'Battle.net')
    BATTLENET_ROAMING = os.path.join(os.environ['APPDATA'], 'Battle.net')
    
    # 战网注册表路径
    BATTLENET_REG_PATH = r"HKCU\Software\Blizzard Entertainment\Battle.net\UnifiedAuth"
    BATTLENET_REG_FULL_PATH = r"HKCU\Software\Blizzard Entertainment\Battle.net"
    
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
    
    def detect_current_version(self) -> str:
        """检测当前活跃的战网版本：'cn'=国服, 'global'=国际服"""
        # 检查当前登录的邮箱，国服邮箱通常是手机号
        config_path = os.path.join(self.BATTLENET_ROAMING, "Battle.net.config")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8-sig') as f:
                    config = json.load(f)
                email = config.get('Client', {}).get('SavedAccountNames', '').split(',')[0]
                # 如果邮箱包含@且不是纯数字，认为是国际服
                if email and '@' in email and not email.split('@')[0].isdigit():
                    return "global"
            except:
                pass
        
        # 默认返回国服
        return "cn"
    
    def get_paths_for_version(self, version: str) -> tuple:
        """获取指定版本的路径（国服和国际服共用同一目录）"""
        return self.BATTLENET_EXE, self.BATTLENET_LOCAL, self.BATTLENET_ROAMING
    
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
        从配置文件和日志中提取账号信息（同时检查国服和国际服路径）
        """
        result = {"account_name": None, "email": None, "battletag": None}
        
        # 先清理无效junction
        self._cleanup_invalid_junctions()
        
        # 国服和国际服共用同一目录
        paths_to_check = [
            (self.BATTLENET_LOCAL, self.BATTLENET_ROAMING)
        ]
        
        for local_path, roaming_path in paths_to_check:
            try:
                # 从Battle.net.config读取SavedAccountNames
                config_path = os.path.join(roaming_path, "Battle.net.config")
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8-sig') as f:
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
                logs_dir = os.path.join(local_path, "Logs")
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
                
                # 如果找到了账号信息，退出循环
                if result["email"] or result["battletag"]:
                    break
            except Exception as e:
                print(f"读取账号信息失败: {e}")
        
        return result
    
    def get_account_local_dir(self, account_id: str) -> str:
        """获取账号的LocalAppData目录"""
        return os.path.join(self.accounts_dir, account_id, "LocalAppData")
    
    def get_account_roaming_dir(self, account_id: str) -> str:
        """获取账号的Roaming目录"""
        return os.path.join(self.accounts_dir, account_id, "Roaming")
    
    def get_account_reg_file(self, account_id: str) -> str:
        """获取账号的注册表备份文件路径"""
        return os.path.join(self.accounts_dir, account_id, "battlenet_reg.reg")
    
    def backup_registry(self, account_id: str) -> bool:
        """备份战网相关注册表到账号目录"""
        reg_file = self.get_account_reg_file(account_id)
        try:
            result = subprocess.run(
                ['reg', 'export', self.BATTLENET_REG_PATH, reg_file, '/y'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        except Exception as e:
            print(f"备份注册表失败: {e}")
            return False
    
    def restore_registry(self, account_id: str) -> bool:
        """从账号目录恢复战网相关注册表"""
        reg_file = self.get_account_reg_file(account_id)
        if not os.path.exists(reg_file):
            return False
        try:
            # 读取备份中的令牌名称
            with open(reg_file, 'r', encoding='utf-16') as f:
                content = f.read()
            
            import re
            token_match = re.search(r'"([A-F0-9]{8})"=', content)
            if not token_match:
                return False
            target_token = token_match.group(1)
            
            # 删除除目标令牌外的所有其他令牌
            current_tokens = self._get_unified_auth_tokens()
            for token in current_tokens:
                if token != target_token:
                    subprocess.run(
                        ['reg', 'delete', self.BATTLENET_REG_PATH, '/v', token, '/f'],
                        capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
                    )
            
            # 导入目标账号的令牌（会覆盖或添加）
            result = subprocess.run(
                ['reg', 'import', reg_file],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        except Exception as e:
            print(f"恢复注册表失败: {e}")
            return False
    
    def get_account_full_reg_file(self, account_id: str) -> str:
        """获取账号的完整注册表备份文件路径（国际服用）"""
        return os.path.join(self.accounts_dir, account_id, "battlenet_full_reg.reg")
    
    def backup_full_registry(self, account_id: str) -> bool:
        """备份完整的战网注册表（国际服用）"""
        reg_file = self.get_account_full_reg_file(account_id)
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(reg_file), exist_ok=True)
            result = subprocess.run(
                ['reg', 'export', self.BATTLENET_REG_FULL_PATH, reg_file, '/y'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            # 写入调试日志
            debug_log = os.path.join(self.accounts_dir, "reg_debug.log")
            with open(debug_log, 'a', encoding='utf-8') as f:
                f.write(f"backup_full_registry: {account_id}\n")
                f.write(f"  路径: {reg_file}\n")
                f.write(f"  返回码: {result.returncode}\n")
                f.write(f"  stdout: {result.stdout}\n")
                f.write(f"  stderr: {result.stderr}\n")
            return result.returncode == 0
        except Exception as e:
            print(f"备份完整注册表失败: {e}")
            return False
    
    def restore_full_registry(self, account_id: str) -> bool:
        """恢复完整的战网注册表（国际服用）"""
        reg_file = self.get_account_full_reg_file(account_id)
        debug_log = os.path.join(self.accounts_dir, "restore_debug.log")
        
        with open(debug_log, 'a', encoding='utf-8') as f:
            f.write(f"\n=== restore_full_registry({account_id}) ===\n")
            f.write(f"reg_file: {reg_file}\n")
            f.write(f"exists: {os.path.exists(reg_file)}\n")
        
        if not os.path.exists(reg_file):
            return False
        try:
            # 只删除UnifiedAuth，保留EncryptionKey和Identity
            del_result = subprocess.run(
                ['reg', 'delete', self.BATTLENET_REG_PATH, '/f'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            # 导入备份（会添加/覆盖UnifiedAuth）
            result = subprocess.run(
                ['reg', 'import', reg_file],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            with open(debug_log, 'a', encoding='utf-8') as f:
                f.write(f"delete UnifiedAuth: {del_result.returncode}\n")
                f.write(f"import: {result.returncode}\n")
                f.write(f"stderr: {result.stderr}\n")
            
            return result.returncode == 0
        except Exception as e:
            with open(debug_log, 'a', encoding='utf-8') as f:
                f.write(f"error: {e}\n")
            return False
    
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
        
        # 创建空的Battle.net目录（不使用junction）
        os.makedirs(self.BATTLENET_LOCAL, exist_ok=True)
        os.makedirs(self.BATTLENET_ROAMING, exist_ok=True)
        
        # 记录临时状态
        self.current_account_id = temp_id
        self._save_current_account(temp_id)
        
        return temp_id
    
    def save_current_as_account(self, nickname: str) -> str:
        """
        将当前登录状态保存为新账号
        从Battle.net目录复制数据到账号目录（不使用junction，保护数据安全）
        """
        import uuid
        
        # 检查Battle.net目录是否有数据
        if not os.path.exists(self.BATTLENET_LOCAL) or not os.listdir(self.BATTLENET_LOCAL):
            # 尝试使用create_account_from_current
            return self.create_account_from_current(nickname)
        
        # 生成正式账号ID
        account_id = str(uuid.uuid4())[:8]
        local_dir = self.get_account_local_dir(account_id)
        roaming_dir = self.get_account_roaming_dir(account_id)
        
        try:
            # 关闭战网
            if self.is_battlenet_running():
                self.close_battlenet()
                time.sleep(2)
            
            # 创建账号目录
            os.makedirs(local_dir, exist_ok=True)
            os.makedirs(roaming_dir, exist_ok=True)
            
            # 从Battle.net目录复制数据到账号目录（保存备份）
            subprocess.run(
                ['robocopy', self.BATTLENET_LOCAL, local_dir, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                ['robocopy', self.BATTLENET_ROAMING, roaming_dir, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 清理临时目录（如果有）
            if self.current_account_id and self.current_account_id.startswith("temp_"):
                temp_dir = os.path.join(self.accounts_dir, self.current_account_id)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
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
        
        # 获取账号版本对应的路径
        version = self.accounts[account_id].get('version', 'cn')
        _, local_path, roaming_path = self.get_paths_for_version(version)
        
        local_dir = self.get_account_local_dir(account_id)
        roaming_dir = self.get_account_roaming_dir(account_id)
        
        try:
            # 关闭战网
            if self.is_battlenet_running():
                self.close_battlenet()
                time.sleep(2)
            
            # 删除旧的账号数据
            if os.path.exists(local_dir):
                shutil.rmtree(local_dir, ignore_errors=True)
            if os.path.exists(roaming_dir):
                shutil.rmtree(roaming_dir, ignore_errors=True)
            
            os.makedirs(local_dir, exist_ok=True)
            os.makedirs(roaming_dir, exist_ok=True)
            
            # 使用robocopy复制当前战网数据到账号目录
            if os.path.exists(local_path):
                subprocess.run(
                    ['robocopy', local_path, local_dir, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/XD', 'Logs'],
                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
            if os.path.exists(roaming_path):
                subprocess.run(
                    ['robocopy', roaming_path, roaming_dir, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            # 仅国服账号备份注册表
            if version == "cn":
                self.backup_registry(account_id)
            
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
    
    def _get_current_email_from_config(self, roaming_path: str) -> str:
        """从config文件获取当前登录的邮箱（SavedAccountNames的第一个）"""
        config_path = os.path.join(roaming_path, "Battle.net.config")
        if not os.path.exists(config_path):
            return None
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
            saved_names = config.get('Client', {}).get('SavedAccountNames', '')
            if saved_names:
                emails = [e.strip() for e in saved_names.split(',') if e.strip()]
                if emails:
                    return emails[0]
        except Exception as e:
            print(f"读取config失败: {e}")
        return None
    
    def _set_first_email_in_config(self, roaming_path: str, email: str) -> bool:
        """修改config文件，将指定邮箱移到SavedAccountNames的第一位"""
        config_path = os.path.join(roaming_path, "Battle.net.config")
        if not os.path.exists(config_path):
            return False
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
            
            saved_names = config.get('Client', {}).get('SavedAccountNames', '')
            emails = [e.strip() for e in saved_names.split(',') if e.strip()]
            
            # 移除已存在的邮箱，然后添加到第一位
            if email in emails:
                emails.remove(email)
            emails.insert(0, email)
            
            config['Client']['SavedAccountNames'] = ','.join(emails)
            
            with open(config_path, 'w', encoding='utf-8-sig') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            return False
    
    def _get_unified_auth_tokens(self) -> list:
        """获取当前UnifiedAuth中的所有令牌名称"""
        try:
            result = subprocess.run(
                ['reg', 'query', self.BATTLENET_REG_PATH],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            tokens = []
            for line in result.stdout.split('\n'):
                if 'REG_BINARY' in line:
                    # 提取令牌名称（第一个字段）
                    parts = line.strip().split()
                    if parts:
                        tokens.append(parts[0])
            return tokens
        except:
            return []
    
    def _clear_global_session_registry(self) -> bool:
        """清除国际服的会话相关注册表项，强制使用SavedAccountNames"""
        try:
            # 删除Launch Options\Pro下的会话相关项
            reg_path = r"HKCU\Software\Blizzard Entertainment\Battle.net\Launch Options\Pro"
            for value_name in ['ACCOUNT', 'ACCOUNT_STATE', 'WEB_TOKEN', 'ACCOUNT_TS', 'GAME_ACCOUNT']:
                subprocess.run(
                    ['reg', 'delete', reg_path, '/v', value_name, '/f'],
                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
            return True
        except Exception as e:
            print(f"清除注册表失败: {e}")
            return False
    
    def _get_current_account_id_folder(self, local_path: str) -> str:
        """获取当前登录账号的专属文件夹ID（BrowserCaches下最近修改的编号文件夹）"""
        browser_caches = os.path.join(local_path, "BrowserCaches")
        if not os.path.exists(browser_caches):
            return None
        
        latest_folder = None
        latest_time = None
        
        for item in os.listdir(browser_caches):
            item_path = os.path.join(browser_caches, item)
            if os.path.isdir(item_path) and item != "common" and item.isdigit():
                # 获取文件夹内最近修改的文件时间
                try:
                    for root, dirs, files in os.walk(item_path):
                        for f in files:
                            file_path = os.path.join(root, f)
                            mtime = os.path.getmtime(file_path)
                            if latest_time is None or mtime > latest_time:
                                latest_time = mtime
                                latest_folder = item
                except:
                    pass
        
        return latest_folder
    
    def create_account_from_current(self, nickname: str, force_version: str = None) -> str:
        """
        从当前登录状态创建新账号
        force_version: 强制指定版本 ("cn" 或 "global")
        国服：复制数据目录 + 备份注册表
        国际服：只记录邮箱（切换时修改config中邮箱顺序）
        """
        import uuid
        account_id = str(uuid.uuid4())[:8]
        
        # 检测当前版本（如果指定了force_version则使用指定版本）
        version = force_version if force_version else self.detect_current_version()
        exe_path, local_path, roaming_path = self.get_paths_for_version(version)
        
        try:
            # 清理无效junction
            self._cleanup_invalid_junctions()
            
            now = datetime.now().isoformat()
            
            # 国服和国际服共用同一目录，统一处理
            current_email = self._get_current_email_from_config(roaming_path)
            
            # 复制数据目录
            local_dir = self.get_account_local_dir(account_id)
            roaming_dir = self.get_account_roaming_dir(account_id)
            
            if os.path.exists(local_dir):
                shutil.rmtree(local_dir, ignore_errors=True)
            if os.path.exists(roaming_dir):
                shutil.rmtree(roaming_dir, ignore_errors=True)
            
            os.makedirs(local_dir, exist_ok=True)
            os.makedirs(roaming_dir, exist_ok=True)
            
            subprocess.run(
                ['robocopy', local_path, local_dir, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                ['robocopy', roaming_path, roaming_dir, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 清理旧令牌，只保留当前账号的令牌
            current_tokens = self._get_unified_auth_tokens()
            if len(current_tokens) > 1:
                for token in current_tokens[:-1]:
                    subprocess.run(
                        ['reg', 'delete', self.BATTLENET_REG_PATH, '/v', token, '/f'],
                        capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
                    )
            
            # 备份注册表
            self.backup_full_registry(account_id)
            
            self.accounts[account_id] = {
                "nickname": nickname,
                "created_time": now,
                "last_login": now,
                "logged_in": True,
                "version": version,
                "email": current_email or ""
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
        切换到指定账号
        国服：复制数据目录 + 恢复注册表
        国际服：只修改config中的邮箱顺序（战网会自动登录第一个邮箱）
        """
        if account_id not in self.accounts:
            return False, "账号不存在"
        
        # 获取账号的版本类型（默认国服）
        version = self.accounts[account_id].get('version', 'cn')
        exe_path, local_path, roaming_path = self.get_paths_for_version(version)
        
        # 关闭战网
        if self.is_battlenet_running():
            self.close_battlenet()
            time.sleep(3)
        
        try:
            # 国服和国际服共用同一目录，统一处理
            local_dir = self.get_account_local_dir(account_id)
            roaming_dir = self.get_account_roaming_dir(account_id)
            
            if not os.path.exists(local_dir):
                return False, "账号LocalAppData目录不存在"
            
            if not os.path.exists(roaming_dir):
                return False, "账号Roaming目录不存在"
            
            # 删除当前目录
            self._remove_dir_or_junction(local_path)
            self._remove_dir_or_junction(roaming_path)
            
            # 确保父目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            os.makedirs(os.path.dirname(roaming_path), exist_ok=True)
            
            time.sleep(0.5)
            
            # 完全镜像同步
            subprocess.run(
                ['robocopy', local_dir, local_path, '/MIR', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                ['robocopy', roaming_dir, roaming_path, '/MIR', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 确保config中正确的邮箱在第一位
            email = self.accounts[account_id].get('email')
            if email:
                self._set_first_email_in_config(roaming_path, email)
            
            # 恢复注册表令牌
            self.restore_full_registry(account_id)
            
            # 记录当前活跃账号和切换时间
            self.current_account_id = account_id
            self._save_current_account(account_id)
            
            # 更新最后登录时间
            self.accounts[account_id]['last_login'] = datetime.now().isoformat()
            self._save_accounts()
            
            # 启动战网（根据账号版本指定地区）
            region = "KR" if version == "global" else "CN"
            self.start_battlenet(region=region)
            
            version_name = "国际服" if version == "global" else "国服"
            nickname = self.accounts[account_id]['nickname']
            return True, f"已切换到{version_name}账号【{nickname}】"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"切换失败: {e}"
    
    def _update_saved_account_names(self, current_account_id: str, roaming_path: str = None):
        """更新SavedAccountNames，确保包含所有已保存账号的邮箱，当前账号排在第一位"""
        try:
            if roaming_path is None:
                roaming_path = self.BATTLENET_ROAMING
            config_path = os.path.join(roaming_path, "Battle.net.config")
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
