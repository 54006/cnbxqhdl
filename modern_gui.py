"""
暴雪战网账号切换器 - 现代PyQt5界面（无边框版）
"""
import sys
import os
import ctypes
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QMessageBox,
    QInputDialog, QGraphicsDropShadowEffect, QSizePolicy, QDialog,
    QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette, QPixmap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isolated_switcher import IsolatedSwitcher, is_admin


# 颜色主题
COLORS = {
    'bg': '#f5f7fa',
    'sidebar': '#ffffff',
    'card': '#e8f4f8',
    'card_hover': '#d4eef5',
    'primary': '#00b4d8',
    'primary_dark': '#0096c7',
    'secondary': '#0ea5e9',
    'success': '#48bb78',
    'warning': '#ed8936',
    'danger': '#fc8181',
    'text': '#2d3748',
    'text_light': '#718096',
    'white': '#ffffff',
    'border': '#e2e8f0'
}

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg']};
}}

QWidget#sidebar {{
    background-color: {COLORS['sidebar']};
    border-right: 1px solid {COLORS['border']};
    border-top-left-radius: 15px;
    border-bottom-left-radius: 15px;
}}

QLabel#title {{
    color: {COLORS['text']};
    font-size: 20px;
    font-weight: bold;
}}

QLabel#subtitle {{
    color: {COLORS['text_light']};
    font-size: 12px;
}}

QPushButton#primaryBtn {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton#primaryBtn:hover {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton#secondaryBtn {{
    background-color: {COLORS['white']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 13px;
}}

QPushButton#secondaryBtn:hover {{
    background-color: {COLORS['bg']};
}}

QPushButton#dangerBtn {{
    background-color: {COLORS['danger']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 13px;
}}

QPushButton#dangerBtn:hover {{
    background-color: #f56565;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QWidget#scrollContent {{
    background-color: transparent;
}}
"""


class ModernDialog(QFrame):
    """现代化的对话框"""
    
    def __init__(self, parent, title, message, dialog_type="info", buttons=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowModality(Qt.ApplicationModal)
        self.result = False
        self.setup_ui(title, message, dialog_type, buttons or ["确定"])
        
    def setup_ui(self, title, message, dialog_type, buttons):
        self.setFixedSize(480, 260)
        
        # 主容器
        container = QFrame(self)
        container.setGeometry(10, 10, 460, 240)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 15px;
            }}
        """)
        
        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # 图标和标题
        header = QHBoxLayout()
        
        icon_colors = {"info": COLORS['primary'], "success": COLORS['success'], 
                      "warning": COLORS['warning'], "error": COLORS['danger']}
        icon_texts = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✗"}
        
        icon = QLabel(icon_texts.get(dialog_type, "ℹ"))
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"""
            background-color: {icon_colors.get(dialog_type, COLORS['primary'])};
            color: white;
            border-radius: 20px;
            font-size: 20px;
            font-weight: bold;
        """)
        header.addWidget(icon)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {COLORS['text']};")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # 消息内容
        msg_label = QLabel(message)
        msg_label.setFont(QFont("微软雅黑", 11))
        msg_label.setStyleSheet(f"color: {COLORS['text_light']};")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        for i, btn_text in enumerate(buttons):
            btn = QPushButton(btn_text)
            if i == 0:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['primary']};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 10px 25px;
                        font-size: 13px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['primary_dark']};
                    }}
                """)
                btn.clicked.connect(self.accept)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: white;
                        color: {COLORS['text']};
                        border: 1px solid {COLORS['border']};
                        border-radius: 8px;
                        padding: 10px 25px;
                        font-size: 13px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['bg']};
                    }}
                """)
                btn.clicked.connect(self.reject)
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        
        # 居中显示
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(parent_geo.center().x() - 240, parent_geo.center().y() - 130)
    
    def accept(self):
        self.result = True
        self.close()
    
    def reject(self):
        self.result = False
        self.close()
    
    @staticmethod
    def show_info(parent, title, message):
        dialog = ModernDialog(parent, title, message, "info")
        dialog.exec_()
    
    @staticmethod
    def show_success(parent, title, message):
        dialog = ModernDialog(parent, title, message, "success")
        dialog.exec_()
    
    @staticmethod
    def show_error(parent, title, message):
        dialog = ModernDialog(parent, title, message, "error")
        dialog.exec_()
    
    @staticmethod
    def show_question(parent, title, message):
        dialog = ModernDialog(parent, title, message, "info", ["确定", "取消"])
        dialog.exec_()
        return dialog.result
    
    def exec_(self):
        self.show()
        # 创建事件循环
        from PyQt5.QtCore import QEventLoop
        self._loop = QEventLoop()
        self._loop.exec_()
    
    def closeEvent(self, event):
        if hasattr(self, '_loop') and self._loop.isRunning():
            self._loop.quit()
        event.accept()


class ModernInputDialog(QFrame):
    """现代化的输入对话框"""
    
    def __init__(self, parent, title, message, default_text=""):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowModality(Qt.ApplicationModal)
        self.result = None
        self.setup_ui(title, message, default_text)
        
    def setup_ui(self, title, message, default_text):
        self.setFixedSize(450, 280)
        
        # 主容器
        container = QFrame(self)
        container.setGeometry(10, 10, 430, 260)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 15px;
            }}
        """)
        
        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("微软雅黑", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {COLORS['primary']};")
        layout.addWidget(title_label)
        
        # 消息内容
        msg_label = QLabel(message)
        msg_label.setFont(QFont("微软雅黑", 10))
        msg_label.setStyleSheet(f"color: {COLORS['text_light']};")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # 输入框
        from PyQt5.QtWidgets import QLineEdit
        self.input_field = QLineEdit()
        self.input_field.setText(default_text)
        self.input_field.setFont(QFont("微软雅黑", 12))
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px 15px;
                background-color: {COLORS['bg']};
                color: {COLORS['text']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        layout.addWidget(self.input_field)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        # 居中显示
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(parent_geo.center().x() - 225, parent_geo.center().y() - 140)
        
        # 聚焦输入框
        self.input_field.setFocus()
        self.input_field.selectAll()
    
    def accept(self):
        self.result = self.input_field.text()
        self.close()
    
    def reject(self):
        self.result = None
        self.close()
    
    def exec_(self):
        self.show()
        from PyQt5.QtCore import QEventLoop
        self._loop = QEventLoop()
        self._loop.exec_()
        return QDialog.Accepted if self.result is not None else QDialog.Rejected
    
    def closeEvent(self, event):
        if hasattr(self, '_loop') and self._loop.isRunning():
            self._loop.quit()
        event.accept()
    
    @staticmethod
    def get_text(parent, title, message, default_text=""):
        dialog = ModernInputDialog(parent, title, message, default_text)
        result = dialog.exec_()
        return dialog.result if result == QDialog.Accepted else "", result == QDialog.Accepted


class SaveAccountDialog(QDialog):
    """保存账号对话框，带国际服勾选框"""
    
    def __init__(self, parent, email, default_name):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.result_nickname = ""
        self.is_global = False
        self.setup_ui(email, default_name)
    
    def setup_ui(self, email, default_name):
        self.setFixedSize(450, 280)
        
        container = QFrame(self)
        container.setGeometry(0, 0, 450, 280)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("🎮 保存账号")
        title.setFont(QFont("微软雅黑", 14, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)
        
        # 邮箱信息
        email_label = QLabel(f"邮箱/手机: {email}")
        email_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        layout.addWidget(email_label)
        
        # 昵称输入
        self.nickname_input = QLineEdit()
        self.nickname_input.setText(default_name)
        self.nickname_input.setPlaceholderText("请输入账号昵称")
        self.nickname_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 12px;
                background-color: {COLORS['bg']};
                color: {COLORS['text']};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        layout.addWidget(self.nickname_input)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(parent_geo.center().x() - 225, parent_geo.center().y() - 140)
        
        self.nickname_input.setFocus()
        self.nickname_input.selectAll()
    
    def accept(self):
        self.result_nickname = self.nickname_input.text()
        super().accept()


class SaveGlobalAccountDialog(QDialog):
    """保存国际服账号对话框（简化版，无密码）"""
    
    def __init__(self, parent, email, default_name):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.result_nickname = ""
        self.setup_ui(email, default_name)
    
    def setup_ui(self, email, default_name):
        self.setFixedSize(450, 280)
        
        container = QFrame(self)
        container.setGeometry(0, 0, 450, 280)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("🌐 保存国际服账号")
        title.setFont(QFont("微软雅黑", 14, QFont.Bold))
        title.setStyleSheet(f"color: #9333ea;")
        layout.addWidget(title)
        
        # 邮箱信息
        email_label = QLabel(f"邮箱: {email}")
        email_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        layout.addWidget(email_label)
        
        # 昵称输入
        self.nickname_input = QLineEdit()
        self.nickname_input.setText(default_name)
        self.nickname_input.setPlaceholderText("请输入账号昵称")
        self.nickname_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 12px;
                background-color: {COLORS['bg']};
                color: {COLORS['text']};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: #9333ea;
            }}
        """)
        layout.addWidget(self.nickname_input)
        
        # 提示
        hint = QLabel("🌐 此账号将标记为国际服账号")
        hint.setStyleSheet(f"color: #9333ea; font-size: 11px;")
        layout.addWidget(hint)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        btn_layout.addSpacing(10)
        
        save_btn = QPushButton("确定")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #9333ea;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7e22ce;
            }
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(parent_geo.center().x() - 225, parent_geo.center().y() - 140)
        
        self.nickname_input.setFocus()
        self.nickname_input.selectAll()
    
    def accept(self):
        self.result_nickname = self.nickname_input.text()
        super().accept()


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.settings = settings.copy()
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedSize(500, 350)
        
        container = QFrame(self)
        container.setGeometry(0, 0, 500, 350)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("⚙️ 设置")
        title.setFont(QFont("微软雅黑", 14, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)
        
        # 战网路径设置
        path_label = QLabel("战网安装路径:")
        path_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px;")
        layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(self.settings.get('battlenet_path', r'C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe'))
        self.path_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                background-color: {COLORS['bg']};
                color: {COLORS['text']};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("浏览")
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 15px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # 隐藏邮箱/手机号开关
        self.hide_email_checkbox = QCheckBox("隐藏账号邮箱/手机号")
        self.hide_email_checkbox.setChecked(self.settings.get('hide_email', False))
        self.hide_email_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text']};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {COLORS['border']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
        """)
        layout.addWidget(self.hide_email_checkbox)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        btn_layout.addSpacing(10)
        
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(parent_geo.center().x() - 250, parent_geo.center().y() - 175)
    
    def browse_path(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "选择战网启动程序", 
            r"C:\Program Files (x86)\Battle.net",
            "可执行文件 (*.exe)"
        )
        if path:
            self.path_input.setText(path)
    
    def accept(self):
        self.settings['battlenet_path'] = self.path_input.text()
        self.settings['hide_email'] = self.hide_email_checkbox.isChecked()
        super().accept()
    
    def get_settings(self):
        return self.settings


class AccountCard(QFrame):
    """账号卡片组件"""
    
    clicked = pyqtSignal(str)
    switch_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    rename_clicked = pyqtSignal(str)
    toggle_version_clicked = pyqtSignal(str)
    update_clicked = pyqtSignal(str)
    
    def __init__(self, account_id, nickname, status, email="", last_login="", version="国服", hide_email=False, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.nickname = nickname
        self.status = status
        self.version = version
        self.hide_email = hide_email
        # 处理邮箱显示
        display_email = self.mask_email(email) if hide_email and email else email
        self.setup_ui(display_email, last_login)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def mask_email(self, email):
        """隐藏邮箱/手机号中间部分"""
        if not email:
            return ""
        if '@' in email:
            # 邮箱格式
            parts = email.split('@')
            name = parts[0]
            if len(name) > 2:
                masked = name[0] + '*' * (len(name) - 2) + name[-1]
            else:
                masked = name[0] + '*'
            return masked + '@' + parts[1]
        else:
            # 手机号格式
            if len(email) > 4:
                return email[:3] + '*' * (len(email) - 6) + email[-3:]
            return email
    
    def mouseDoubleClickEvent(self, event):
        """双击切换账号"""
        self.switch_clicked.emit(self.account_id)
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['bg']};
            }}
        """)
        
        switch_action = menu.addAction("🔄 切换")
        update_action = menu.addAction("💾 更新账号数据")
        rename_action = menu.addAction("✏️ 重命名")
        
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ 删除")
        
        action = menu.exec_(self.mapToGlobal(pos))
        
        if action == switch_action:
            self.switch_clicked.emit(self.account_id)
        elif action == update_action:
            self.update_clicked.emit(self.account_id)
        elif action == rename_action:
            self.rename_clicked.emit(self.account_id)
        elif action == delete_action:
            self.delete_clicked.emit(self.account_id)
        
    def setup_ui(self, email, last_login):
        self.setObjectName("accountCard")
        self.setFixedHeight(120)  # 增加高度容纳三个按钮
        self.setCursor(Qt.PointingHandCursor)
        
        # 卡片样式
        self.setStyleSheet(f"""
            QFrame#accountCard {{
                background-color: {COLORS['card']};
                border-radius: 12px;
                border: none;
            }}
            QFrame#accountCard:hover {{
                background-color: {COLORS['card_hover']};
            }}
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # 头像区域
        avatar = QLabel()
        avatar.setFixedSize(60, 60)
        avatar.setStyleSheet(f"""
            background-color: {COLORS['primary']};
            border-radius: 30px;
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setText(self.nickname[0].upper() if self.nickname else "?")
        layout.addWidget(avatar)
        
        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(self.nickname)
        name_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 16px; font-weight: bold;")
        info_layout.addWidget(name_label)
        
        email_label = QLabel(email or "未知邮箱")
        email_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        info_layout.addWidget(email_label)
        
        time_label = QLabel(f"最后登录: {last_login}" if last_login else "")
        time_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px;")
        info_layout.addWidget(time_label)
        
        layout.addLayout(info_layout, 1)
        
        # 版本和状态标签容器
        tags_layout = QVBoxLayout()
        tags_layout.setSpacing(4)
        
        # 版本标签
        version_color = "#9333ea" if self.version == "国际服" else COLORS['primary']
        version_label = QLabel(self.version)
        version_label.setStyleSheet(f"""
            color: white;
            background-color: {version_color};
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 10px;
        """)
        version_label.setFixedHeight(22)
        tags_layout.addWidget(version_label)
        
        # 状态标签
        status_text = "已登录" if self.status else "未登录"
        status_color = COLORS['success'] if self.status else COLORS['warning']
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            color: white;
            background-color: {status_color};
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 10px;
        """)
        status_label.setFixedHeight(22)
        tags_layout.addWidget(status_label)
        
        layout.addLayout(tags_layout)
        
        # 操作按钮
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(5)
        
        switch_btn = QPushButton("切换")
        switch_btn.setFixedSize(70, 32)
        switch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        switch_btn.clicked.connect(lambda: self.switch_clicked.emit(self.account_id))
        btn_layout.addWidget(switch_btn)
        
        rename_btn = QPushButton("重命名")
        rename_btn.setFixedSize(70, 28)
        rename_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border']};
                color: {COLORS['text']};
            }}
        """)
        rename_btn.clicked.connect(lambda: self.rename_clicked.emit(self.account_id))
        btn_layout.addWidget(rename_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setFixedSize(70, 28)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['danger']};
                border: 1px solid {COLORS['danger']};
                border-radius: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
            }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.account_id))
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)


class SwitchThread(QThread):
    """切换账号的后台线程"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, switcher, account_id):
        super().__init__()
        self.switcher = switcher
        self.account_id = account_id
    
    def run(self):
        success, msg = self.switcher.switch_to_account(self.account_id)
        self.finished.emit(success, msg)


class ModernGUI(QMainWindow):
    """现代化的战网账号切换器（无边框可拖拽）"""
    
    def __init__(self):
        super().__init__()
        self.switcher = IsolatedSwitcher()
        self.switch_thread = None
        self.drag_pos = None
        self.settings = self.load_settings()
        self.apply_settings()
        self.setup_ui()
        self.refresh_accounts()
    
    def load_settings(self):
        """加载设置"""
        import json
        settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')
        if getattr(sys, 'frozen', False):
            settings_file = os.path.join(os.path.dirname(sys.executable), 'data', 'settings.json')
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            'battlenet_path': r'C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe',
            'hide_email': False
        }
    
    def save_settings(self):
        """保存设置"""
        import json
        settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')
        if getattr(sys, 'frozen', False):
            settings_file = os.path.join(os.path.dirname(sys.executable), 'data', 'settings.json')
        try:
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def apply_settings(self):
        """应用设置"""
        if self.settings.get('battlenet_path'):
            self.switcher.BATTLENET_EXE = self.settings['battlenet_path']
    
    def get_icon_path(self):
        """获取图标路径（支持打包后的exe）"""
        import sys
        if getattr(sys, 'frozen', False):
            # 打包后，图标在exe同目录或_MEIPASS临时目录
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        
        icon_path = os.path.join(base_path, "006.ico")
        if os.path.exists(icon_path):
            return icon_path
        # 也检查exe同目录
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(os.path.dirname(sys.executable), "006.ico")
            if os.path.exists(icon_path):
                return icon_path
        return None
        
    def setup_ui(self):
        # 无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(850, 620)
        
        # 设置窗口图标
        icon_path = self.get_icon_path()
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 主容器（带圆角和阴影）
        container = QWidget()
        self.setCentralWidget(container)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        
        # 内容框架
        self.main_frame = QFrame()
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setStyleSheet(f"""
            QFrame#mainFrame {{
                background-color: {COLORS['bg']};
                border-radius: 15px;
            }}
        """)
        
        # 添加阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 5)
        self.main_frame.setGraphicsEffect(shadow)
        
        container_layout.addWidget(self.main_frame)
        
        # 主布局
        main_layout = QHBoxLayout(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧边栏
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # 右侧内容区
        content = self.create_content()
        main_layout.addWidget(content, 1)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.drag_pos = None
    
    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 15, 20, 30)
        layout.setSpacing(15)
        
        # 窗口控制按钮
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(8)
        
        close_btn = QPushButton("●")
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff5f57;
                border: none;
                border-radius: 8px;
                font-size: 8px;
                color: transparent;
            }}
            QPushButton:hover {{
                color: #800000;
            }}
        """)
        close_btn.clicked.connect(self.close)
        ctrl_layout.addWidget(close_btn)
        
        min_btn = QPushButton("●")
        min_btn.setFixedSize(16, 16)
        min_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffbd2e;
                border: none;
                border-radius: 8px;
                font-size: 8px;
                color: transparent;
            }}
            QPushButton:hover {{
                color: #805500;
            }}
        """)
        min_btn.clicked.connect(self.showMinimized)
        ctrl_layout.addWidget(min_btn)
        
        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)
        
        layout.addSpacing(10)
        
        # Logo/标题 - 使用自定义图标
        logo_label = QLabel()
        icon_path = self.get_icon_path()
        if icon_path and os.path.exists(icon_path):
            logo_pixmap = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label.setText("🎮")
            logo_label.setStyleSheet("font-size: 48px;")
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        title = QLabel("国服战网账号切换")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("快速切换多个账号")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(30)
        
        # 保存按钮（主要操作）
        save_btn = QPushButton("💾 保存当前登录")
        save_btn.setFixedHeight(45)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 #6366f1);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary_dark']}, stop:1 #4f46e5);
            }}
            QPushButton:pressed {{
                background: {COLORS['primary_dark']};
            }}
        """)
        save_btn.clicked.connect(self.save_current_login)
        layout.addWidget(save_btn)
        
        # 保存当前登录(国际服)按钮
        save_global_btn = QPushButton("🌐 保存当前登录(国际服)")
        save_global_btn.setFixedHeight(45)
        save_global_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9333ea, stop:1 #7c3aed);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7e22ce, stop:1 #6d28d9);
            }}
            QPushButton:pressed {{
                background: #6b21a8;
            }}
        """)
        save_global_btn.clicked.connect(self.save_current_login_global)
        layout.addWidget(save_global_btn)
        
        layout.addSpacing(15)
        
        # 登录新账号按钮
        new_login_btn = QPushButton("🔄 登录新账号")
        new_login_btn.setFixedHeight(40)
        new_login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['secondary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #0284c7;
            }}
        """)
        new_login_btn.clicked.connect(self.prepare_new_account)
        layout.addWidget(new_login_btn)
        
        # 登录国际服新账号按钮
        global_login_btn = QPushButton("🌐 登录国际服新账号")
        global_login_btn.setFixedHeight(40)
        global_login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #9333ea;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #7e22ce;
            }}
        """)
        global_login_btn.clicked.connect(self.prepare_global_account)
        layout.addWidget(global_login_btn)
        
        layout.addSpacing(15)
        
        # 战网控制按钮
        start_btn = QPushButton("🚀 启动战网")
        start_btn.setFixedHeight(40)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        start_btn.clicked.connect(self.start_battlenet)
        layout.addWidget(start_btn)
        
        close_battlenet_btn = QPushButton("⏹️ 关闭战网")
        close_battlenet_btn.setFixedHeight(40)
        close_battlenet_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #dc2626;
            }}
        """)
        close_battlenet_btn.clicked.connect(self.close_battlenet)
        layout.addWidget(close_battlenet_btn)
        
        # 设置按钮
        settings_btn = QPushButton("⚙️ 设置")
        settings_btn.setFixedHeight(40)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border']};
            }}
        """)
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)
        
        layout.addStretch()
        
        # 状态信息
        admin_text = "✅ 管理员模式" if is_admin() else "⚠️ 普通模式"
        admin_color = COLORS['success'] if is_admin() else COLORS['warning']
        admin_label = QLabel(admin_text)
        admin_label.setStyleSheet(f"color: {admin_color}; font-size: 11px;")
        admin_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(admin_label)
        
        # 作者信息
        author_info = QLabel("免费开源，禁止倒卖\nB站：54006o | QQ：2449995562\n个人站：www.006.kim")
        author_info.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 10px;")
        author_info.setAlignment(Qt.AlignCenter)
        author_info.setWordWrap(True)
        layout.addWidget(author_info)
        
        return sidebar
    
    def create_content(self):
        content = QWidget()
        content.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg']};
                border-top-right-radius: 15px;
                border-bottom-right-radius: 15px;
            }}
        """)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题栏
        header = QHBoxLayout()
        
        title = QLabel("账号列表")
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 24px; font-weight: bold;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.count_label = QLabel("共 0 个账号")
        self.count_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 14px;")
        header.addWidget(self.count_label)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.clicked.connect(self.refresh_accounts)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContent")
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 10, 0)
        self.cards_layout.setSpacing(15)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)
        
        # 使用说明
        help_frame = QFrame()
        help_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['white']};
                border-radius: 10px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        help_layout = QVBoxLayout(help_frame)
        help_layout.setContentsMargins(15, 10, 15, 10)
        
        help_title = QLabel("💡 使用说明")
        help_title.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; font-weight: bold;")
        help_layout.addWidget(help_title)
        
        help_text = QLabel("添加账号：登录战网后点击【保存当前登录】 | 切换：点击账号卡片的【切换】按钮")
        help_text.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_frame)
        
        return content
    
    def refresh_accounts(self):
        # 清除现有卡片
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取账号列表
        accounts = self.switcher.get_all_accounts()
        
        for acc in accounts:
            last_login = acc.get('last_login', '')
            if last_login:
                try:
                    dt = datetime.fromisoformat(last_login)
                    last_login = dt.strftime('%Y-%m-%d %H:%M:%S')  # 精确到秒
                except:
                    pass
            
            email = self.switcher.accounts.get(acc['id'], {}).get('email', '')
            version = self.switcher.accounts.get(acc['id'], {}).get('version', 'cn')
            version_text = "国际服" if version == "global" else "国服"
            
            card = AccountCard(
                acc['id'],
                acc['nickname'],
                acc['logged_in'] and acc['has_data'],
                email,
                last_login,
                version_text,
                self.settings.get('hide_email', False)
            )
            card.switch_clicked.connect(self.switch_account)
            card.delete_clicked.connect(self.delete_account)
            card.rename_clicked.connect(self.rename_account)
            card.toggle_version_clicked.connect(self.toggle_version)
            card.update_clicked.connect(self.update_account_data)
            
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        
        self.count_label.setText(f"共 {len(accounts)} 个账号")
    
    def prepare_new_login(self):
        """准备添加新账号 - 创建干净的临时目录"""
        reply = ModernDialog.show_question(
            self, "准备新登录",
            "这将关闭战网并创建一个干净的环境。\n\n"
            "之后请在战网中登录新账号，\n"
            "登录成功后点击【保存当前登录】。\n\n"
            "确定继续？"
        )
        
        if not reply:
            return
        
        temp_id = self.switcher.prepare_for_new_login()
        if temp_id:
            # 启动战网
            self.switcher.start_battlenet()
            ModernDialog.show_info(
                self, "准备完成",
                "已创建干净的登录环境。\n\n"
                "请在战网中登录账号，\n"
                "登录成功后点击【保存当前登录】保存。"
            )
        else:
            ModernDialog.show_error(self, "错误", "准备新登录失败")
    
    def save_current_login(self):
        """保存当前登录的账号 - 自动创建新的隔离文件夹"""
        if not self.switcher.is_battlenet_running():
            ModernDialog.show_info(self, "提示", "请先启动战网并登录账号")
            return
        
        # 获取当前登录账号信息
        account_info = self.switcher.get_current_logged_account()
        
        if not account_info.get("email") and not account_info.get("battletag"):
            ModernDialog.show_info(self, "提示", "无法识别当前登录的账号\n\n请确保已在战网中登录")
            return
        
        default_name = account_info.get("battletag") or account_info.get("account_name") or "未知账号"
        email = account_info.get("email", "")
        
        # 检查是否已存在相同邮箱的账号
        for acc_id, acc_info in self.switcher.accounts.items():
            if acc_info.get("email") == email:
                reply = ModernDialog.show_question(
                    self, "账号已存在",
                    f"邮箱 {email} 对应的账号已存在\n昵称: {acc_info.get('nickname')}\n\n"
                    "是否更新该账号的数据？（会覆盖旧数据）"
                )
                if reply:
                    # 更新现有账号的数据
                    self.switcher.update_account_data(acc_id)
                    self.switcher.mark_logged_in(acc_id)
                    self.switcher._save_accounts()
                    self.refresh_accounts()
                    ModernDialog.show_success(self, "成功", f"账号【{acc_info.get('nickname')}】数据已更新")
                return
        
        # 保存对话框（国服账号）
        dialog = SaveAccountDialog(self, email, default_name)
        if dialog.exec_() == QDialog.Accepted and dialog.result_nickname:
            nickname = dialog.result_nickname
            
            # 记录保存前已有多少账号
            existing_count = len(self.switcher.accounts)
            
            # 自动创建新文件夹并保存（国服账号）
            account_id = self.switcher.create_account_from_current(nickname, force_version="cn")
            if account_id:
                self.switcher.accounts[account_id]["email"] = email
                self.switcher.accounts[account_id]["battletag"] = account_info.get("battletag")
                self.switcher.accounts[account_id]["version"] = "cn"
                self.switcher._save_accounts()
                self.refresh_accounts()
                
                # 如果之前已有账号，提示需要重新保存
                if existing_count > 0:
                    ModernDialog.show_info(
                        self, "保存成功", 
                        f"已保存账号【{nickname}】\n\n"
                        "⚠️ 重要提示：\n"
                        "由于战网会话机制限制，之前保存的账号可能无法自动登录。\n\n"
                        "请依次登录并重新保存所有之前的账号，\n"
                        "这样所有账号就能正常切换了。"
                    )
                else:
                    ModernDialog.show_success(self, "成功", f"已保存账号【{nickname}】")
            else:
                ModernDialog.show_error(self, "错误", "保存账号数据失败")
    
    def save_current_login_global(self):
        """保存当前登录的国际服账号"""
        if not self.switcher.is_battlenet_running():
            ModernDialog.show_info(self, "提示", "请先启动战网并登录国际服账号")
            return
        
        # 获取当前登录账号信息
        account_info = self.switcher.get_current_logged_account()
        
        # 国际服可能无法自动识别邮箱，使用BattleTag或让用户输入
        default_name = account_info.get("battletag") or account_info.get("account_name") or ""
        email = account_info.get("email") or account_info.get("battletag") or ""
        
        # 检查是否已存在相同邮箱的账号
        for acc_id, acc_info in self.switcher.accounts.items():
            if acc_info.get("email") == email:
                reply = ModernDialog.show_question(
                    self, "账号已存在",
                    f"邮箱 {email} 对应的账号已存在\n昵称: {acc_info.get('nickname')}\n\n"
                    "是否更新该账号的数据？（会覆盖旧数据）"
                )
                if reply:
                    self.switcher.update_account_data(acc_id)
                    self.switcher.mark_logged_in(acc_id)
                    self.switcher._save_accounts()
                    self.refresh_accounts()
                    ModernDialog.show_success(self, "成功", f"账号【{acc_info.get('nickname')}】数据已更新")
                return
        
        # 使用国际服专用对话框
        dialog = SaveGlobalAccountDialog(self, email, default_name)
        if dialog.exec_() == QDialog.Accepted and dialog.result_nickname:
            nickname = dialog.result_nickname
            
            # 强制设置为国际服版本
            account_id = self.switcher.create_account_from_current(nickname, force_version="global")
            if account_id:
                self.switcher.accounts[account_id]["email"] = email
                self.switcher.accounts[account_id]["battletag"] = account_info.get("battletag")
                self.switcher.accounts[account_id]["version"] = "global"
                self.switcher._save_accounts()
                self.refresh_accounts()
                ModernDialog.show_success(self, "成功", f"已保存国际服账号【{nickname}】")
            else:
                ModernDialog.show_error(self, "错误", "保存账号数据失败")
    
    def auto_add_account(self):
        if not self.switcher.is_battlenet_running():
            ModernDialog.show_info(self, "提示", "请先启动战网并登录账号")
            return
        
        account_info = self.switcher.get_current_logged_account()
        
        if not account_info.get("email") and not account_info.get("battletag"):
            ModernDialog.show_info(self, "提示", "无法识别当前登录的账号\n\n请确保已在战网中登录")
            return
        
        default_name = account_info.get("battletag") or account_info.get("account_name") or "未知账号"
        email = account_info.get("email", "")
        
        nickname, ok = ModernInputDialog.get_text(
            self, "🎮 识别到账号",
            f"邮箱/手机: {email}\nBattleTag: {account_info.get('battletag', '未知')}\n\n请输入账号昵称：",
            default_name
        )
        
        if ok and nickname:
            # 检查是否已存在
            for acc_id, acc_info in self.switcher.accounts.items():
                if acc_info.get("email") == email:
                    reply = ModernDialog.show_question(
                        self, "账号已存在",
                        f"邮箱 {email} 对应的账号已存在\n昵称: {acc_info.get('nickname')}\n\n是否更新该账号的登录状态？"
                    )
                    if reply:
                        self.switcher.mark_logged_in(acc_id)
                        self.switcher.accounts[acc_id]["email"] = email
                        self.switcher.accounts[acc_id]["battletag"] = account_info.get("battletag")
                        self.switcher._save_accounts()
                        self.refresh_accounts()
                        ModernDialog.show_success(self, "成功", f"账号【{acc_info.get('nickname')}】登录状态已更新")
                    return
            
            # 创建新账号
            account_id = self.switcher.create_account_from_current(nickname)
            if account_id:
                self.switcher.accounts[account_id]["email"] = email
                self.switcher.accounts[account_id]["battletag"] = account_info.get("battletag")
                self.switcher.mark_logged_in(account_id)
                self.switcher._save_accounts()
                self.refresh_accounts()
                ModernDialog.show_success(self, "成功", f"已添加并保存账号【{nickname}】\n邮箱: {email}")
            else:
                ModernDialog.show_error(self, "错误", "保存账号数据失败")
    
    def prepare_new_account(self):
        """清除当前登录状态，准备登录新账号（保留地区设置）"""
        reply = ModernDialog.show_question(
            self, "登录新账号",
            "这将清除当前的登录状态，让你可以登录新账号。\n\n"
            "⚠️ 请确保已保存当前账号再继续。\n\n"
            "确定继续？"
        )
        if not reply:
            return
        
        import shutil
        import json
        import time
        
        # 关闭战网
        if self.switcher.is_battlenet_running():
            self.switcher.close_battlenet()
            time.sleep(2)
        
        # 清除Roaming下的BrowserCaches
        roaming_cache = os.path.join(self.switcher.BATTLENET_ROAMING, "BrowserCaches")
        if os.path.exists(roaming_cache):
            shutil.rmtree(roaming_cache, ignore_errors=True)
        
        # 清除LocalAppData下的BrowserCaches  
        local_cache = os.path.join(self.switcher.BATTLENET_LOCAL, "BrowserCaches")
        if os.path.exists(local_cache):
            shutil.rmtree(local_cache, ignore_errors=True)
        
        # 修改config，清除SavedAccountNames但保留其他设置
        config_path = os.path.join(self.switcher.BATTLENET_ROAMING, "Battle.net.config")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if "Client" in config:
                    config["Client"]["SavedAccountNames"] = ""
                    config["Client"]["AutoLogin"] = "false"
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
            except:
                pass
        
        # 启动战网（指定中国区）
        self.switcher.start_battlenet(region="CN")
        
        ModernDialog.show_info(
            self, "准备完成",
            "已清除登录状态，战网已启动。\n\n"
            "请登录新账号，登录成功后点击【保存当前登录】。"
        )
    
    def prepare_global_account(self):
        """准备登录国际服新账号 - 使用和国服相同的方法"""
        reply = ModernDialog.show_question(
            self, "登录国际服新账号",
            "这将关闭战网并创建一个干净的环境。\n\n"
            "之后请在战网中登录国际服账号，\n"
            "登录成功后点击【保存当前登录(国际服)】。\n\n"
            "确定继续？"
        )
        if not reply:
            return
        
        # 使用和国服相同的方法创建干净环境
        temp_id = self.switcher.prepare_for_new_login()
        if temp_id:
            # 启动战网（指定KR区）
            self.switcher.start_battlenet(region="KR")
            ModernDialog.show_info(
                self, "准备完成",
                "已创建干净的登录环境，战网已启动（国际服）。\n\n"
                "请登录国际服账号，\n"
                "登录成功后点击【保存当前登录(国际服)】保存。"
            )
        else:
            ModernDialog.show_error(self, "错误", "准备新登录失败")
    
    def manual_add_account(self):
        nickname, ok = ModernInputDialog.get_text(self, "➕ 创建账号", "请输入账号昵称（便于识别）：", "")
        if ok and nickname:
            account_id = self.switcher.create_account(nickname)
            self.refresh_accounts()
            
            reply = ModernDialog.show_question(
                self, "创建成功",
                f"已创建账号【{nickname}】\n\n是否立即切换到该账号进行登录？"
            )
            if reply:
                self.switch_account(account_id)
    
    def switch_account(self, account_id):
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        
        # 禁用UI
        self.setEnabled(False)
        self.setWindowTitle(f"暴雪战网账号切换器 - 正在切换到 {nickname}...")
        
        self.switch_thread = SwitchThread(self.switcher, account_id)
        self.switch_thread.finished.connect(lambda s, m: self.on_switch_finished(s, m, account_id))
        self.switch_thread.start()
    
    def on_switch_finished(self, success, msg, account_id):
        self.setEnabled(True)
        self.setWindowTitle("暴雪战网账号切换器")
        
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        version = acc_info.get('version', 'cn')
        
        if success:
            if acc_info.get('logged_in'):
                ModernDialog.show_success(self, "切换成功", f"已切换到账号【{nickname}】\n\n战网应该会自动登录")
            else:
                ModernDialog.show_info(
                    self, "切换成功",
                    f"已切换到账号【{nickname}】\n\n请在战网中完成登录\n登录成功后再次点击【保存当前登录】保存状态"
                )
        else:
            ModernDialog.show_error(self, "切换失败", f"切换失败: {msg}")
        
        self.refresh_accounts()
    
    def rename_account(self, account_id):
        """重命名账号"""
        acc_info = self.switcher.accounts.get(account_id, {})
        old_nickname = acc_info.get('nickname', '未知')
        
        new_nickname, ok = ModernInputDialog.get_text(
            self, "重命名账号",
            f"当前昵称: {old_nickname}\n\n请输入新昵称：",
            old_nickname
        )
        
        if ok and new_nickname and new_nickname != old_nickname:
            self.switcher.accounts[account_id]['nickname'] = new_nickname
            self.switcher._save_accounts()
            self.refresh_accounts()
            ModernDialog.show_success(self, "成功", f"账号已重命名为【{new_nickname}】")
    
    def toggle_version(self, account_id):
        """切换账号的版本标记（国服/国际服）"""
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        current_version = acc_info.get('version', 'cn')
        
        if current_version == 'cn':
            new_version = 'global'
            new_version_text = '国际服'
        else:
            new_version = 'cn'
            new_version_text = '国服'
        
        self.switcher.accounts[account_id]['version'] = new_version
        self.switcher._save_accounts()
        self.refresh_accounts()
        ModernDialog.show_success(self, "成功", f"账号【{nickname}】已标记为{new_version_text}")
    
    def update_account_data(self, account_id):
        """更新账号数据（从当前战网状态覆盖保存的数据）"""
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        
        if not self.switcher.is_battlenet_running():
            ModernDialog.show_info(self, "提示", "请先启动战网并登录该账号")
            return
        
        reply = ModernDialog.show_question(
            self, "更新账号数据",
            f"确定要用当前战网的登录状态覆盖账号【{nickname}】的数据吗？\n\n"
            "⚠️ 请确保当前战网已登录的是该账号"
        )
        if reply:
            self.switcher.update_account_data(account_id)
            self.switcher.mark_logged_in(account_id)
            self.switcher._save_accounts()
            self.refresh_accounts()
            ModernDialog.show_success(self, "成功", f"账号【{nickname}】数据已更新")
    
    def delete_account(self, account_id):
        acc_info = self.switcher.accounts.get(account_id, {})
        nickname = acc_info.get('nickname', '未知')
        
        reply = ModernDialog.show_question(
            self, "确认删除",
            f"确定要删除账号【{nickname}】吗？\n\n这将删除该账号的所有数据"
        )
        if reply:
            self.switcher.delete_account(account_id)
            self.refresh_accounts()
    
    def start_battlenet(self):
        if self.switcher.start_battlenet():
            pass  # 静默成功
        else:
            ModernDialog.show_error(self, "错误", "启动战网失败")
    
    def close_battlenet(self):
        self.switcher.close_battlenet()
    
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec_() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            self.apply_settings()
            self.save_settings()
            self.refresh_accounts()  # 刷新以应用隐藏邮箱设置
            ModernDialog.show_success(self, "成功", "设置已保存")


def main():
    # 请求管理员权限
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)
        except:
            pass
    
    app = QApplication(sys.argv)
    app.setFont(QFont("微软雅黑", 10))
    
    window = ModernGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
