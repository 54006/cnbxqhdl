"""
暴雪战网账号切换器 - 核心模块
通过备份/恢复整个Battle.net本地数据实现账号切换
"""
import os
import shutil
import json
import subprocess
import time
import psutil
from datetime import datetime
from config import DATA_DIR, ensure_dirs


class BattleNetSwitcher:
    """战网账号切换器"""
    
    # 战网相关路径
    BATTLENET_EXE = r"C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe"
    # 需要备份的目录
    BATTLENET_LOCAL = os.path.join(os.environ['LOCALAPPDATA'], 'Battle.net')
    BATTLENET_ROAMING = os.path.join(os.environ['APPDATA'], 'Battle.net')
    BROWSER_CACHES_PATH = os.path.join(os.environ['LOCALAPPDATA'], 'Battle.net', 'BrowserCaches')
    ACCOUNT_DATA_PATH = os.path.join(os.environ['LOCALAPPDATA'], 'Battle.net', 'Account')
    
    def __init__(self):
        ensure_dirs()
        self.backups_dir = os.path.join(DATA_DIR, "battlenet_backups")
        self.accounts_file = os.path.join(DATA_DIR, "switcher_accounts.json")
        os.makedirs(self.backups_dir, exist_ok=True)
        self.accounts = self._load_accounts()
    
    def _load_accounts(self) -> dict:
        """加载账号配置"""
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_accounts(self):
        """保存账号配置"""
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, ensure_ascii=False, indent=2)
    
    def is_battlenet_running(self) -> bool:
        """检查战网客户端是否在运行"""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'battle.net' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
    
    def close_battlenet(self) -> bool:
        """关闭战网客户端"""
        closed = False
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] and 'battle.net' in proc.info['name'].lower():
                    proc.terminate()
                    closed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if closed:
            time.sleep(2)  # 等待进程完全退出
        return closed
    
    def start_battlenet(self) -> bool:
        """启动战网客户端"""
        if os.path.exists(self.BATTLENET_EXE):
            try:
                subprocess.Popen([self.BATTLENET_EXE])
                return True
            except Exception as e:
                print(f"启动战网失败: {e}")
        return False
    
    def get_current_account_id(self) -> str:
        """获取当前登录的账号ID（从最近修改的Account文件夹判断）"""
        if not os.path.exists(self.ACCOUNT_DATA_PATH):
            return None
        
        latest_time = 0
        latest_account = None
        
        for folder in os.listdir(self.ACCOUNT_DATA_PATH):
            folder_path = os.path.join(self.ACCOUNT_DATA_PATH, folder)
            if os.path.isdir(folder_path):
                mtime = os.path.getmtime(folder_path)
                if mtime > latest_time:
                    latest_time = mtime
                    latest_account = folder
        
        return latest_account
    
    def backup_current_state(self, account_id: str, nickname: str) -> bool:
        """
        备份当前登录状态（备份整个Battle.net本地数据）
        
        Args:
            account_id: 账号ID（用户自定义或自动生成）
            nickname: 账号昵称
        
        Returns:
            bool: 是否成功
        """
        if not os.path.exists(self.BATTLENET_LOCAL):
            print("Battle.net目录不存在")
            return False
        
        # 创建备份目录
        backup_path = os.path.join(self.backups_dir, account_id)
        backup_local = os.path.join(backup_path, "LocalAppData")
        backup_roaming = os.path.join(backup_path, "Roaming")
        
        try:
            # 如果已存在则先删除
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            os.makedirs(backup_path)
            
            # 复制LocalAppData\Battle.net（排除Logs目录减少大小）
            def ignore_logs(dir, files):
                return ['Logs'] if 'Logs' in files else []
            shutil.copytree(self.BATTLENET_LOCAL, backup_local, ignore=ignore_logs)
            
            # 复制Roaming\Battle.net（配置文件）
            if os.path.exists(self.BATTLENET_ROAMING):
                shutil.copytree(self.BATTLENET_ROAMING, backup_roaming)
            
            # 保存账号信息
            bn_account_id = self.get_current_account_id()
            self.accounts[account_id] = {
                "nickname": nickname,
                "battlenet_account_id": bn_account_id,
                "backup_time": datetime.now().isoformat(),
                "backup_path": backup_path
            }
            self._save_accounts()
            
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False
    
    def restore_state(self, account_id: str) -> bool:
        """
        恢复账号状态（恢复整个Battle.net本地数据）
        
        Args:
            account_id: 账号ID
        
        Returns:
            bool: 是否成功
        """
        if account_id not in self.accounts:
            print(f"账号 {account_id} 不存在")
            return False
        
        backup_path = os.path.join(self.backups_dir, account_id)
        backup_local = os.path.join(backup_path, "LocalAppData")
        backup_roaming = os.path.join(backup_path, "Roaming")
        
        if not os.path.exists(backup_local):
            print(f"备份文件不存在: {backup_local}")
            return False
        
        try:
            # 删除当前Battle.net本地数据（保留Logs）
            if os.path.exists(self.BATTLENET_LOCAL):
                for item in os.listdir(self.BATTLENET_LOCAL):
                    if item != 'Logs':
                        item_path = os.path.join(self.BATTLENET_LOCAL, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
            
            # 恢复LocalAppData备份
            for item in os.listdir(backup_local):
                src = os.path.join(backup_local, item)
                dst = os.path.join(self.BATTLENET_LOCAL, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            # 恢复Roaming备份
            if os.path.exists(backup_roaming):
                if os.path.exists(self.BATTLENET_ROAMING):
                    shutil.rmtree(self.BATTLENET_ROAMING)
                shutil.copytree(backup_roaming, self.BATTLENET_ROAMING)
            
            return True
        except Exception as e:
            print(f"恢复失败: {e}")
            return False
    
    def switch_account(self, account_id: str) -> tuple:
        """
        切换账号
        
        Args:
            account_id: 目标账号ID
        
        Returns:
            tuple: (成功与否, 消息)
        """
        if account_id not in self.accounts:
            return False, "账号不存在"
        
        # 1. 关闭战网
        if self.is_battlenet_running():
            self.close_battlenet()
            time.sleep(1)
        
        # 2. 恢复备份
        if not self.restore_state(account_id):
            return False, "恢复备份失败"
        
        # 3. 启动战网
        if self.start_battlenet():
            return True, "切换成功，战网已启动"
        else:
            return True, "备份已恢复，请手动启动战网"
    
    def get_all_accounts(self) -> list:
        """获取所有账号列表"""
        result = []
        for account_id, info in self.accounts.items():
            backup_path = os.path.join(self.backups_dir, account_id)
            result.append({
                "id": account_id,
                "nickname": info.get("nickname", "未知"),
                "backup_time": info.get("backup_time", ""),
                "has_backup": os.path.exists(backup_path)
            })
        return result
    
    def delete_account(self, account_id: str) -> bool:
        """删除账号及其备份"""
        if account_id in self.accounts:
            del self.accounts[account_id]
            self._save_accounts()
        
        backup_path = os.path.join(self.backups_dir, account_id)
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        
        return True
    
    def add_account(self, nickname: str) -> str:
        """添加新账号（仅创建记录，需要登录后保存）"""
        import uuid
        account_id = str(uuid.uuid4())[:8]
        self.accounts[account_id] = {
            "nickname": nickname,
            "backup_time": None,
            "battlenet_account_id": None
        }
        self._save_accounts()
        return account_id


if __name__ == "__main__":
    # 测试
    switcher = BattleNetSwitcher()
    print(f"战网运行中: {switcher.is_battlenet_running()}")
    print(f"当前账号ID: {switcher.get_current_account_id()}")
    print(f"已保存账号: {switcher.get_all_accounts()}")
