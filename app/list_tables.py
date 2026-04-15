import sqlite3

def list_tables_and_columns(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        print(f"表名: {table_name}")
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = cursor.fetchall()
        headers = [col[1] for col in columns]
        print(f"表头: {headers}\n")
    conn.close()

if __name__ == '__main__':
    db_path = r'e:\PycharmProjects\moosas_backend\weather_data.db'
    list_tables_and_columns(db_path)
