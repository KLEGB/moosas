import sqlite3

def count_epw_files(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM epw_files')
    count = cursor.fetchone()[0]
    conn.close()
    return count

if __name__ == '__main__':
    db_path = r'e:\PycharmProjects\moosas_backend\weather_data.db'
    print('EPW 文件总数:', count_epw_files(db_path))
