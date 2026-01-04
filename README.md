AI帮忙
# 国服战网账号切换器

一个用于管理暴雪战网(中国区)多账号的工具。保存完整的登录会话数据，实现一键切换账号自动登录。

## 功能特点

- 🔐 **保存登录会话**：保存完整的Battle.net会话数据，切换后自动登录
- 🔄 **一键切换账号**：点击切换按钮或双击卡片即可切换
- 📝 **账号管理**：添加、重命名、删除账号
- 🚀 **启动战网**：快捷启动暴雪战网客户端
- 💾 **本地存储**：所有数据保存在本地，保护隐私安全
- 🎨 **现代UI**：美观的PyQt5无边框界面

## 下载使用

### 方式一：直接下载EXE（推荐）
从 [Releases](../../releases) 页面下载 `国服战网账号切换.exe`，双击运行即可。

### 方式二：从源码运行
```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/仓库名.git
cd 仓库名

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python modern_gui.py
```

## 使用说明

### 添加账号
1. 点击【启动战网】
2. 在战网中登录账号
3. 点击【保存当前登录】

### 切换账号
- 点击账号卡片上的【切换】按钮
- 或者双击账号卡片
- 
## 技术原理

程序通过隔离存储每个账号的Battle.net数据目录（包括BrowserCaches和配置文件），切换账号时将对应账号的数据复制到Battle.net的数据目录，从而实现自动登录。

## 文件结构

```
├── modern_gui.py        # 主程序（PyQt5界面）
├── isolated_switcher.py # 账号切换核心逻辑
├── requirements.txt     # 依赖列表
├── build.spec          # PyInstaller打包配置
├── 006.ico             # 程序图标
└── data/               # 数据目录（运行时创建）
    ├── isolated_accounts.json  # 账号列表
    ├── switcher_state.json     # 状态文件
    └── isolated_accounts/      # 账号数据目录
```

## 免责声明

本工具仅供学习和个人使用，请勿用于任何违反暴雪/网易服务条款的行为。使用本工具产生的任何后果由使用者自行承担。

## 开源协议

MIT License
