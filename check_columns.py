import sqlite3

DB_NAME = 'sahl_new.db'  # تأكد من أن اسم قاعدة البيانات صحيح

def list_users_columns():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users);")
    columns = c.fetchall()
    print("أعمدة جدول 'users':")
    for col in columns:
        print(f"Column name: {col[1]}, Type: {col[2]}")
    conn.close()




def test_query():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = '''
    SELECT u.id, sp.name, u.phone, u.whatsapp, u.email, sp.profile_picture
    FROM users u
    JOIN service_providers sp ON u.id = sp.user_id
    WHERE u.role = 'service_provider'
    '''
    try:
        c.execute(query)
        results = c.fetchall()
        print("نتائج الاستعلام:")
        for row in results:
            print(row)
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")
    finally:
        conn.close()

def list_users_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users;")
    rows = c.fetchall()
    print("بيانات جدول 'users':")
    for row in rows:
        print(row)
    conn.close()


if __name__ == '__main__':
    list_users_columns()   # يعرض الأعمدة قبل الإضافة
    list_users_columns()   # يعرض الأعمدة بعد الإضافة للتحقق
    list_users_data()      # يعرض بيانات جدول 'users'
    test_query()           # يختبر الاستعلام الذي يسبب المشكلة
