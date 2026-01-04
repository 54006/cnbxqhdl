"""分析战网客户端的账号数据存储"""
import sqlite3
import os
import json

ACCOUNT_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'Battle.net', 'Account')

def analyze_account_db(account_id):
    """分析单个账号的数据库"""
    db_path = os.path.join(ACCOUNT_DIR, str(account_id), 'account.db')
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"    找到 {len(tables)} 个表: {tables}")
        
        result = {'account_id': account_id, 'tables': {}}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT * FROM [{table}] LIMIT 5")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                result['tables'][table] = {
                    'columns': columns,
                    'sample_rows': rows[:2]
                }
                print(f"    表 {table}: 列={columns}")
                for row in rows[:2]:
                    print(f"      {row}")
            except Exception as te:
                print(f"    表 {table} 读取错误: {te}")
        
        conn.close()
        return result
    except Exception as e:
        print(f"    数据库错误: {e}")
        return {'error': str(e)}

def main():
    # 获取最近使用的账号
    accounts = []
    for folder in os.listdir(ACCOUNT_DIR):
        folder_path = os.path.join(ACCOUNT_DIR, folder)
        if os.path.isdir(folder_path):
            db_path = os.path.join(folder_path, 'account.db')
            if os.path.exists(db_path):
                mtime = os.path.getmtime(db_path)
                accounts.append((folder, mtime))
    
    # 按修改时间排序
    accounts.sort(key=lambda x: x[1], reverse=True)
    
    print(f"找到 {len(accounts)} 个账号数据库")
    print("\n最近使用的3个账号:")
    
    for account_id, mtime in accounts[:3]:
        print(f"\n=== 账号ID: {account_id} ===")
        result = analyze_account_db(account_id)
        if result and 'tables' in result:
            for table, info in result['tables'].items():
                print(f"  表: {table}")
                print(f"    列: {info['columns']}")
                if info['sample_rows']:
                    print(f"    示例数据: {info['sample_rows'][0][:3]}...")

if __name__ == '__main__':
    main()
