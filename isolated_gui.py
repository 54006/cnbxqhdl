"""
暴雪战网账号切换器 - 独立数据目录版GUI
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import ctypes
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isolated_switcher import IsolatedSwitcher, is_admin


class IsolatedGUI:
    """独立数据目录切换器GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("暴雪战网账号切换器 v3.0 (独立目录版)")
        self.root.geometry("700x500")
        
        self.switcher = IsolatedSwitcher()
        self.current_account = None
        
        self.setup_styles()
        self.create_ui()
        self.refresh_list()
        
        # 检查管理员权限
        if not is_admin():
            messagebox.showwarning("权限提示", 
                "建议以管理员身份运行以获得完整功能\n"
                "右键点击程序 -> 以管理员身份运行")
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('微软雅黑', 14, 'bold'))
        style.configure('Info.TLabel', font=('微软雅黑', 9))
        style.configure('Big.TButton', padding=10, font=('微软雅黑', 10))
    
    def create_ui(self):
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main, text="🎮 暴雪战网账号切换器 (独立目录版)", style='Title.TLabel').pack(pady=(0, 5))
        
        # 说明
        info_text = ("每个账号使用独立的数据目录，登录状态互不影响\n"
                    "首次使用：创建账号 → 切换到该账号 → 在战网中登录 → 点击确认登录")
        ttk.Label(main, text=info_text, style='Info.TLabel', justify='center').pack(pady=(0, 10))
        
        # 状态
        status_frame = ttk.Frame(main)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="就绪", style='Info.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        self.admin_label = ttk.Label(status_frame, 
            text="✅ 管理员" if is_admin() else "⚠️ 非管理员", 
            style='Info.TLabel',
            foreground='green' if is_admin() else 'orange')
        self.admin_label.pack(side=tk.RIGHT)
        
        # 账号列表
        list_frame = ttk.LabelFrame(main, text="账号列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ('nickname', 'status', 'last_login')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        self.tree.heading('nickname', text='账号昵称')
        self.tree.heading('status', text='状态')
        self.tree.heading('last_login', text='最后登录')
        self.tree.column('nickname', width=200)
        self.tree.column('status', width=150)
        self.tree.column('last_login', width=180)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<Double-1>', lambda e: self.switch_account())
        
        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)
        
        row1 = ttk.Frame(btn_frame)
        row1.pack(fill=tk.X, pady=3)
        
        ttk.Button(row1, text="🔍 识别添加", command=self.auto_add_account, style='Big.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="➕ 手动创建", command=self.create_account, style='Big.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="🔄 切换账号", command=self.switch_account, style='Big.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="🗑️ 删除", command=self.delete_account, style='Big.TButton').pack(side=tk.LEFT, padx=5)
        
        row2 = ttk.Frame(btn_frame)
        row2.pack(fill=tk.X, pady=3)
        
        ttk.Button(row2, text="🚀 启动战网", command=self.start_battlenet, style='Big.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="⏹️ 关闭战网", command=self.close_battlenet, style='Big.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="🔃 刷新", command=self.refresh_list, style='Big.TButton').pack(side=tk.LEFT, padx=5)
        
        # 使用说明
        help_frame = ttk.LabelFrame(main, text="使用说明", padding="5")
        help_frame.pack(fill=tk.X, pady=5)
        
        help_text = ("方法一（推荐）：登录战网 → 点击【识别添加】→ 自动保存账号\n"
                    "方法二：点击【手动创建】→ 切换到该账号 → 在战网登录\n"
                    "切换账号：选中账号 → 点击【切换账号】→ 自动登录")
        ttk.Label(help_frame, text=help_text, style='Info.TLabel', justify='left').pack(anchor='w')
    
    def set_status(self, msg):
        self.status_label.config(text=msg)
    
    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        accounts = self.switcher.get_all_accounts()
        for acc in accounts:
            if acc['logged_in']:
                status = "✅ 已登录" if acc['has_data'] else "⚠️ 需重新登录"
            else:
                status = "❌ 未登录"
            
            last_login = acc.get('last_login', '')
            if last_login:
                try:
                    dt = datetime.fromisoformat(last_login)
                    last_login = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            self.tree.insert('', tk.END, iid=acc['id'], values=(
                acc['nickname'], status, last_login or '-'
            ))
        
        self.set_status(f"共 {len(accounts)} 个账号")
    
    def get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个账号")
            return None
        return sel[0]
    
    def create_account(self):
        """手动创建账号"""
        nickname = simpledialog.askstring("创建账号", "请输入账号昵称（便于识别）：", parent=self.root)
        if nickname:
            account_id = self.switcher.create_account(nickname)
            self.refresh_list()
            
            if messagebox.askyesno("创建成功", 
                f"已创建账号【{nickname}】\n\n"
                "是否立即切换到该账号进行登录？"):
                self.current_account = account_id
                self.do_switch(account_id)
    
    def auto_add_account(self):
        """自动识别当前登录的账号并添加"""
        # 检查战网是否在运行
        if not self.switcher.is_battlenet_running():
            messagebox.showwarning("提示", "请先启动战网并登录账号")
            return
        
        # 获取当前登录的账号信息
        account_info = self.switcher.get_current_logged_account()
        
        if not account_info.get("email") and not account_info.get("battletag"):
            messagebox.showwarning("提示", 
                "无法识别当前登录的账号\n\n"
                "请确保已在战网中登录")
            return
        
        # 生成默认昵称
        default_name = account_info.get("battletag") or account_info.get("account_name") or "未知账号"
        email = account_info.get("email", "")
        
        # 显示识别结果，让用户确认或修改昵称
        nickname = simpledialog.askstring("识别到账号", 
            f"已识别当前登录账号：\n"
            f"邮箱/手机: {email}\n"
            f"BattleTag: {account_info.get('battletag', '未知')}\n\n"
            f"请输入账号昵称（可修改）：",
            initialvalue=default_name,
            parent=self.root)
        
        if nickname:
            # 检查是否已存在相同邮箱的账号
            for acc_id, acc_info in self.switcher.accounts.items():
                if acc_info.get("email") == email:
                    if messagebox.askyesno("账号已存在", 
                        f"邮箱 {email} 对应的账号已存在\n"
                        f"昵称: {acc_info.get('nickname')}\n\n"
                        "是否更新该账号的登录状态？"):
                        self.switcher.mark_logged_in(acc_id)
                        self.switcher.accounts[acc_id]["email"] = email
                        self.switcher.accounts[acc_id]["battletag"] = account_info.get("battletag")
                        self.switcher._save_accounts()
                        self.refresh_list()
                        messagebox.showinfo("成功", f"账号【{acc_info.get('nickname')}】登录状态已更新")
                    return
            
            # 创建新账号并复制当前目录数据
            account_id = self.switcher.create_account_from_current(nickname)
            if account_id:
                self.switcher.accounts[account_id]["email"] = email
                self.switcher.accounts[account_id]["battletag"] = account_info.get("battletag")
                self.switcher.mark_logged_in(account_id)
                self.switcher._save_accounts()
                
                self.refresh_list()
                messagebox.showinfo("成功", 
                    f"已添加并保存账号【{nickname}】\n"
                    f"邮箱: {email}\n\n"
                    "之后可直接切换到该账号")
            else:
                messagebox.showerror("错误", "保存账号数据失败")
    
    def switch_account(self):
        account_id = self.get_selected()
        if not account_id:
            return
        
        self.current_account = account_id
        self.do_switch(account_id)
    
    def do_switch(self, account_id):
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        
        self.set_status(f"正在切换到 {nickname}...")
        
        def switch_thread():
            success, msg = self.switcher.switch_to_account(account_id)
            
            def update_ui():
                if success:
                    self.set_status(f"已切换到 {nickname}")
                    if not acc_info.get('logged_in'):
                        messagebox.showinfo("切换成功", 
                            f"已切换到账号【{nickname}】\n\n"
                            "请在战网中完成登录\n"
                            "登录成功后点击【确认已登录】按钮")
                    else:
                        messagebox.showinfo("切换成功", 
                            f"已切换到账号【{nickname}】\n\n"
                            "战网应该会自动登录")
                else:
                    self.set_status("切换失败")
                    messagebox.showerror("错误", f"切换失败: {msg}")
                self.refresh_list()
            
            self.root.after(0, update_ui)
        
        threading.Thread(target=switch_thread, daemon=True).start()
    
    def confirm_login(self):
        account_id = self.get_selected()
        if not account_id:
            return
        
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        
        if messagebox.askyesno("确认登录", 
            f"确认账号【{nickname}】已在战网中登录成功？\n\n"
            "这将保存该账号的登录状态"):
            self.switcher.mark_logged_in(account_id)
            self.refresh_list()
            messagebox.showinfo("成功", 
                f"账号【{nickname}】登录状态已保存！\n\n"
                "之后切换到该账号将自动登录")
    
    def delete_account(self):
        account_id = self.get_selected()
        if not account_id:
            return
        
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        
        if messagebox.askyesno("确认删除", 
            f"确定要删除账号【{nickname}】吗？\n\n"
            "这将删除该账号的所有数据"):
            self.switcher.delete_account(account_id)
            self.refresh_list()
            self.set_status(f"已删除账号: {nickname}")
    
    def start_battlenet(self):
        if self.switcher.start_battlenet():
            self.set_status("战网已启动")
        else:
            messagebox.showerror("错误", "启动战网失败")
    
    def close_battlenet(self):
        if self.switcher.close_battlenet():
            self.set_status("战网已关闭")
        else:
            self.set_status("战网未在运行")
    
    def run(self):
        self.root.mainloop()


def main():
    # 请求管理员权限
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)
        except:
            pass  # 用户拒绝了UAC提示，继续以普通权限运行
    
    app = IsolatedGUI()
    app.run()


if __name__ == "__main__":
    main()
