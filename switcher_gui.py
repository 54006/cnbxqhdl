"""
暴雪战网账号切换器 - 图形界面
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from battlenet_switcher import BattleNetSwitcher


class SwitcherGUI:
    """战网账号切换器GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("暴雪战网账号切换器 v2.0")
        self.root.geometry("650x450")
        self.root.resizable(True, True)
        
        self.switcher = BattleNetSwitcher()
        
        self.setup_styles()
        self.create_ui()
        self.refresh_list()
    
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('微软雅黑', 14, 'bold'))
        style.configure('Info.TLabel', font=('微软雅黑', 9))
        style.configure('Big.TButton', padding=8, font=('微软雅黑', 10))
    
    def create_ui(self):
        """创建界面"""
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main, text="🎮 暴雪战网账号切换器", style='Title.TLabel').pack(pady=(0, 5))
        ttk.Label(main, text="备份登录状态，一键切换账号，无需重新登录", style='Info.TLabel').pack(pady=(0, 10))
        
        # 状态显示
        status_frame = ttk.Frame(main)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="", style='Info.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        self.battlenet_status = ttk.Label(status_frame, text="", style='Info.TLabel')
        self.battlenet_status.pack(side=tk.RIGHT)
        self.update_battlenet_status()
        
        # 账号列表
        list_frame = ttk.LabelFrame(main, text="已保存的账号", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ('nickname', 'status', 'backup_time')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        self.tree.heading('nickname', text='账号昵称')
        self.tree.heading('status', text='状态')
        self.tree.heading('backup_time', text='备份时间')
        self.tree.column('nickname', width=150)
        self.tree.column('status', width=100)
        self.tree.column('backup_time', width=180)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<Double-1>', lambda e: self.switch_account())
        
        # 按钮区域
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)
        
        row1 = ttk.Frame(btn_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Button(row1, text="➕ 添加账号", command=self.add_account, style='Big.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(row1, text="💾 保存当前登录", command=self.save_current, style='Big.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(row1, text="🔄 切换账号", command=self.switch_account, style='Big.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(row1, text="🗑️ 删除", command=self.delete_account, style='Big.TButton').pack(side=tk.LEFT, padx=3)
        
        row2 = ttk.Frame(btn_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Button(row2, text="🚀 启动战网", command=self.start_battlenet, style='Big.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="⏹️ 关闭战网", command=self.close_battlenet, style='Big.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(row2, text="🔃 刷新", command=self.refresh_list, style='Big.TButton').pack(side=tk.LEFT, padx=3)
        
        # 使用说明
        help_text = "使用方法：1.登录战网 → 2.点击【保存当前登录】 → 3.下次点击【切换账号】即可"
        ttk.Label(main, text=help_text, style='Info.TLabel', foreground='gray').pack(pady=5)
    
    def update_battlenet_status(self):
        """更新战网状态显示"""
        if self.switcher.is_battlenet_running():
            self.battlenet_status.config(text="🟢 战网运行中", foreground='green')
        else:
            self.battlenet_status.config(text="🔴 战网未运行", foreground='red')
        self.root.after(3000, self.update_battlenet_status)
    
    def refresh_list(self):
        """刷新账号列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        accounts = self.switcher.get_all_accounts()
        for acc in accounts:
            status = "✅ 已备份" if acc['has_backup'] else "❌ 未备份"
            backup_time = acc.get('backup_time', '')
            if backup_time:
                try:
                    dt = datetime.fromisoformat(backup_time)
                    backup_time = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            self.tree.insert('', tk.END, iid=acc['id'], values=(
                acc['nickname'], status, backup_time or '-'
            ))
        
        self.set_status(f"已加载 {len(accounts)} 个账号")
    
    def get_selected(self):
        """获取选中的账号"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个账号")
            return None
        return sel[0]
    
    def set_status(self, msg):
        """设置状态栏"""
        self.status_label.config(text=msg)
    
    def add_account(self):
        """添加账号"""
        nickname = simpledialog.askstring("添加账号", "请输入账号昵称（便于识别）：", parent=self.root)
        if nickname:
            self.switcher.add_account(nickname)
            self.refresh_list()
            messagebox.showinfo("成功", f"已添加账号【{nickname}】\n\n请登录该账号后，点击【保存当前登录】")
    
    def save_current(self):
        """保存当前登录状态"""
        account_id = self.get_selected()
        if not account_id:
            return
        
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        
        if not self.switcher.is_battlenet_running():
            messagebox.showwarning("提示", "请先启动战网并登录要保存的账号")
            return
        
        if messagebox.askyesno("确认保存", 
            f"确定要保存当前登录状态到账号【{nickname}】吗？\n\n"
            "这将覆盖该账号之前的备份"):
            
            self.set_status("正在保存...")
            
            def do_save():
                if self.switcher.backup_current_state(account_id, nickname):
                    self.root.after(0, lambda: messagebox.showinfo("成功", 
                        f"账号【{nickname}】登录状态已保存！\n\n下次可直接切换到此账号"))
                    self.root.after(0, self.refresh_list)
                else:
                    self.root.after(0, lambda: messagebox.showerror("错误", "保存失败"))
                self.root.after(0, lambda: self.set_status("就绪"))
            
            threading.Thread(target=do_save, daemon=True).start()
    
    def switch_account(self):
        """切换账号"""
        account_id = self.get_selected()
        if not account_id:
            return
        
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        
        if not acc_info.get('backup_time'):
            messagebox.showwarning("提示", f"账号【{nickname}】还没有保存登录状态\n\n请先登录并【保存当前登录】")
            return
        
        if messagebox.askyesno("确认切换", 
            f"确定要切换到账号【{nickname}】吗？\n\n"
            "这将关闭当前战网并启动新账号"):
            
            self.set_status(f"正在切换到 {nickname}...")
            
            def do_switch():
                success, msg = self.switcher.switch_account(account_id)
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("成功", f"已切换到账号【{nickname}】\n\n{msg}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("错误", f"切换失败: {msg}"))
                self.root.after(0, lambda: self.set_status("就绪"))
            
            threading.Thread(target=do_switch, daemon=True).start()
    
    def delete_account(self):
        """删除账号"""
        account_id = self.get_selected()
        if not account_id:
            return
        
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        
        if messagebox.askyesno("确认删除", f"确定要删除账号【{nickname}】及其备份吗？"):
            self.switcher.delete_account(account_id)
            self.refresh_list()
            self.set_status(f"已删除账号: {nickname}")
    
    def start_battlenet(self):
        """启动战网"""
        if self.switcher.start_battlenet():
            self.set_status("战网已启动")
        else:
            messagebox.showerror("错误", "启动战网失败，请检查安装路径")
    
    def close_battlenet(self):
        """关闭战网"""
        if self.switcher.close_battlenet():
            self.set_status("战网已关闭")
        else:
            self.set_status("战网未在运行")
    
    def run(self):
        """运行程序"""
        self.root.mainloop()


def main():
    app = SwitcherGUI()
    app.run()


if __name__ == "__main__":
    main()
