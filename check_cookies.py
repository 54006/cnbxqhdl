"""检查战网内置浏览器的Cookies"""
import sqlite3
import os
import shutil

# 复制cookies文件（因为原文件可能被锁定）
src = os.path.join(os.environ['LOCALAPPDATA'], 'Battle.net', 'BrowserCaches', 'common', 'Network', 'Cookies')
dst = os.path.join(os.environ['TEMP'], 'bn_cookies_copy.db')

try:
    shutil.copy2(src, dst)
    print(f"已复制Cookies文件到: {dst}")
    
    conn = sqlite3.connect(dst)
    cursor = conn.cursor()
    
    # 获取表结构
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"表: {tables}")
    
    # 查看cookies表结构和内容
    if 'cookies' in tables:
        cursor.execute("PRAGMA table_info(cookies)")
        columns = [r[1] for r in cursor.fetchall()]
        print(f"cookies表列: {columns}")
        
        # 查看battlenet相关的cookies
        cursor.execute("SELECT host_key, name, value, encrypted_value, expires_utc FROM cookies WHERE host_key LIKE '%battlenet%' OR host_key LIKE '%battle.net%'")
        print("\n战网相关Cookies:")
        for row in cursor.fetchall():
            host, name, value, enc_value, expires = row
            has_value = "有明文" if value else "无明文"
            has_enc = f"加密({len(enc_value)}字节)" if enc_value else "无加密"
            print(f"  {host} | {name} | {has_value} | {has_enc}")
    
    conn.close()
except Exception as e:
    print(f"错误: {e}")
