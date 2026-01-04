"""
暴雪战网账号管理工具 - 主程序
支持多账号Cookie保存和快速切换
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from account_manager import AccountManager
from browser_controller import BrowserController
from cookie_handler import CookieHandler
from token_manager import TokenManager
from protocol_handler import ProtocolHandler


class BattleNetAccountManager:
    """暴雪战网账号管理器 GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("暴雪战网账号管理器")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 初始化管理器
        self.account_manager = AccountManager()
        self.token_manager = TokenManager()
        self.protocol_handler = ProtocolHandler()
        self.browser_controller = None
        self.current_account_id = None
        
        # 设置样式
        self.setup_styles()
        
        # 创建UI
        self.create_ui()
        
        # 加载账号列表
        self.refresh_account_list()
    
    def setup_styles(self):
        """设置UI样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义按钮样式
        style.configure('Primary.TButton', padding=10, font=('微软雅黑', 10))
        style.configure('Success.TButton', padding=10, font=('微软雅黑', 10))
        style.configure('Danger.TButton', padding=10, font=('微软雅黑', 10))
        
        # 标签样式
        style.configure('Title.TLabel', font=('微软雅黑', 14, 'bold'))
        style.configure('Info.TLabel', font=('微软雅黑', 9))
    
    def create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎮 暴雪战网账号管理器", style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        # 说明文字
        info_text = "保存登录状态，快速切换账号，无需重复输入验证码"
        info_label = ttk.Label(main_frame, text=info_text, style='Info.TLabel')
        info_label.pack(pady=(0, 10))
        
        # 账号列表框架
        list_frame = ttk.LabelFrame(main_frame, text="账号列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建Treeview
        columns = ('nickname', 'status', 'last_login', 'login_count')
        self.account_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        self.account_tree.heading('nickname', text='账号昵称')
        self.account_tree.heading('status', text='登录状态')
        self.account_tree.heading('last_login', text='上次登录')
        self.account_tree.heading('login_count', text='登录次数')
        
        self.account_tree.column('nickname', width=150)
        self.account_tree.column('status', width=100)
        self.account_tree.column('last_login', width=150)
        self.account_tree.column('login_count', width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar.set)
        
        self.account_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 双击切换账号
        self.account_tree.bind('<Double-1>', self.on_double_click)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # 第一行按钮
        row1 = ttk.Frame(btn_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Button(row1, text="➕ 添加账号", command=self.add_account, 
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="🔐 登录并保存", command=self.login_and_save,
                   style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="🔄 切换账号", command=self.switch_account,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="🗑️ 删除账号", command=self.delete_account,
                   style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        
        # 第二行按钮
        row2 = ttk.Frame(btn_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Button(row2, text="🚀 启动战网客户端", command=self.launch_battlenet,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="🔃 刷新列表", command=self.refresh_account_list,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="✏️ 编辑账号", command=self.edit_account,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def refresh_account_list(self):
        """刷新账号列表"""
        # 清空现有列表
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        
        # 重新加载账号
        self.account_manager = AccountManager()
        accounts = self.account_manager.get_all_accounts()
        
        for account in accounts:
            # 检查是否有保存的浏览器配置文件
            has_profile = self.browser_controller_has_profile(account['id'])
            status = "✅ 已保存" if has_profile else "❌ 未登录"
            
            last_login = account.get('last_login', '')
            if last_login:
                try:
                    dt = datetime.fromisoformat(last_login)
                    last_login = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            else:
                last_login = "从未登录"
            
            self.account_tree.insert('', tk.END, iid=account['id'], values=(
                account.get('nickname', '未命名'),
                status,
                last_login,
                account.get('login_count', 0)
            ))
        
        self.set_status(f"已加载 {len(accounts)} 个账号")
    
    def get_selected_account(self):
        """获取选中的账号ID"""
        selection = self.account_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个账号")
            return None
        return selection[0]
    
    def add_account(self):
        """添加新账号"""
        nickname = simpledialog.askstring("添加账号", "请输入账号昵称（用于识别）：",
                                          parent=self.root)
        if nickname:
            note = simpledialog.askstring("添加账号", "请输入备注（可选）：",
                                          parent=self.root)
            account_id = self.account_manager.add_account(nickname, note or "")
            self.refresh_account_list()
            self.set_status(f"已添加账号: {nickname}")
            messagebox.showinfo("成功", f"账号 '{nickname}' 已添加\n\n请点击【登录并保存】来保存登录状态")
    
    def login_and_save(self):
        """登录并保存登录回调URL"""
        account_id = self.get_selected_account()
        if not account_id:
            return
        
        account = self.account_manager.get_account(account_id)
        nickname = account.get('nickname', '未知')
        
        # 弹出说明窗口
        self.show_capture_dialog(account_id, nickname)
    
    def show_capture_dialog(self, account_id, nickname):
        """为账号打开独立浏览器进行登录"""
        self.set_status(f"正在为账号 {nickname} 打开登录浏览器...")
        
        def do_login():
            try:
                self.browser_controller = BrowserController()
                if self.browser_controller.open_login_for_account(account_id):
                    self.root.after(0, lambda: self.wait_for_profile_login(account_id, nickname))
                else:
                    self.set_status("打开浏览器失败")
                    self.root.after(0, lambda: messagebox.showerror("错误", "无法打开浏览器"))
            except Exception as e:
                self.set_status(f"错误: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"操作失败: {e}"))
        
        threading.Thread(target=do_login, daemon=True).start()
    
    def wait_for_profile_login(self, account_id, nickname):
        """等待用户在独立浏览器中完成登录"""
        result = messagebox.askokcancel("等待登录", 
            f"已为账号【{nickname}】打开独立浏览器\n\n"
            "请在浏览器中完成登录：\n"
            "1. 输入账号密码\n"
            "2. 完成验证码验证\n"
            "3. 看到登录成功页面后\n\n"
            "点击【确定】保存登录状态\n"
            "点击【取消】放弃")
        
        if result:
            # 登录状态已保存在浏览器配置文件中
            self.account_manager.record_login(account_id)
            self.set_status(f"账号 {nickname} 登录状态已保存")
            messagebox.showinfo("成功", 
                f"账号【{nickname}】登录状态已保存！\n\n"
                "登录信息保存在独立浏览器配置中\n"
                "下次切换账号时会自动使用此登录状态")
            self.refresh_account_list()
        
        # 关闭浏览器
        if self.browser_controller:
            self.browser_controller.close()
            self.browser_controller = None
    
    def switch_account(self):
        """切换账号 - 使用账号独立的浏览器配置文件"""
        account_id = self.get_selected_account()
        if not account_id:
            return
        
        account = self.account_manager.get_account(account_id)
        nickname = account.get('nickname', '未知')
        
        # 检查是否有保存的浏览器配置
        if not self.browser_controller_has_profile(account_id):
            messagebox.showwarning("提示", 
                f"账号【{nickname}】还没有保存登录状态\n\n"
                "请先点击【登录并保存】进行首次登录")
            return
        
        self.set_status(f"正在切换到账号: {nickname}...")
        
        def do_switch():
            try:
                self.browser_controller = BrowserController()
                if self.browser_controller.switch_to_account(account_id):
                    self.account_manager.record_login(account_id)
                    self.set_status(f"已切换到账号: {nickname}")
                    self.root.after(0, lambda: messagebox.showinfo("成功", 
                        f"已打开账号【{nickname}】的浏览器\n\n"
                        "浏览器中应该已自动登录\n"
                        "如果显示登录页面，说明登录已过期，需重新登录保存"))
                    self.root.after(0, self.refresh_account_list)
                else:
                    self.set_status("切换失败")
                    self.root.after(0, lambda: messagebox.showerror("错误", "打开浏览器失败"))
            except Exception as e:
                self.set_status(f"错误: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"切换失败: {e}"))
        
        threading.Thread(target=do_switch, daemon=True).start()
    
    def browser_controller_has_profile(self, account_id):
        """检查账号是否有浏览器配置文件"""
        from config import DATA_DIR
        profile_dir = os.path.join(DATA_DIR, "profiles", f"profile_{account_id}")
        return os.path.exists(profile_dir)
    
    def delete_account(self):
        """删除账号"""
        account_id = self.get_selected_account()
        if not account_id:
            return
        
        account = self.account_manager.get_account(account_id)
        
        if messagebox.askyesno("确认删除", 
            f"确定要删除账号 '{account.get('nickname')}' 吗？\n\n"
            "这将同时删除保存的登录状态"):
            self.account_manager.remove_account(account_id)
            self.refresh_account_list()
            self.set_status(f"已删除账号: {account.get('nickname')}")
    
    def edit_account(self):
        """编辑账号"""
        account_id = self.get_selected_account()
        if not account_id:
            return
        
        account = self.account_manager.get_account(account_id)
        
        new_nickname = simpledialog.askstring("编辑账号", "请输入新的昵称：",
                                              initialvalue=account.get('nickname', ''),
                                              parent=self.root)
        if new_nickname:
            self.account_manager.update_account(account_id, nickname=new_nickname)
            self.refresh_account_list()
            self.set_status(f"已更新账号昵称")
    
    def launch_battlenet(self):
        """启动战网客户端"""
        self.set_status("正在启动战网客户端...")
        
        try:
            controller = BrowserController()
            if controller.launch_battlenet_client():
                self.set_status("战网客户端已启动")
            else:
                messagebox.showwarning("提示", "未找到战网客户端\n\n请手动启动战网")
                self.set_status("未找到战网客户端")
        except Exception as e:
            self.set_status(f"启动失败: {e}")
    
    def on_double_click(self, event):
        """双击切换账号"""
        self.switch_account()
    
    def set_status(self, message):
        """设置状态栏消息"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def run(self):
        """运行程序"""
        self.root.mainloop()
    
    def on_closing(self):
        """关闭程序时清理资源"""
        if self.browser_controller:
            self.browser_controller.close()
        self.root.destroy()


def main():
    app = BattleNetAccountManager()
    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.run()


if __name__ == "__main__":
    main()
