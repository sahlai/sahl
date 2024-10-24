import sys
import sqlite3
from datetime import datetime
import hashlib
import os
import re
import unicodedata
from werkzeug.security import generate_password_hash, check_password_hash



DB_NAME = 'sahl_new.db'


#1
def create_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        # جدول الدول
        c.execute('''CREATE TABLE IF NOT EXISTS countries
                     (id INTEGER PRIMARY KEY,
                      name TEXT UNIQUE,
                      is_active INTEGER DEFAULT 1)''')

        # جدول المدن
        c.execute('''CREATE TABLE IF NOT EXISTS cities
                     (id INTEGER PRIMARY KEY,
                      name TEXT NOT NULL,
                      country_id INTEGER,
                      is_active INTEGER DEFAULT 1,
                      FOREIGN KEY (country_id) REFERENCES countries(id))''')

        # جدول الأحياء
        c.execute('''CREATE TABLE IF NOT EXISTS districts
                     (id INTEGER PRIMARY KEY,
                      name TEXT NOT NULL,
                      city_id INTEGER,
                      is_active INTEGER DEFAULT 1,
                      FOREIGN KEY (city_id) REFERENCES cities(id))''')
    #المستخدمين
        c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone TEXT UNIQUE,
    whatsapp TEXT UNIQUE,
    role TEXT NOT NULL CHECK(role IN ('end_user', 'service_provider', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')


        # جدول مقدمي الخدمات
        c.execute('''CREATE TABLE IF NOT EXISTS service_providers (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            profile_picture TEXT,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id))''')

        # جدول الخدمات التي يقدمها مقدم الخدمة
        c.execute('''CREATE TABLE IF NOT EXISTS service_provider_services (
            id INTEGER PRIMARY KEY,
            service_provider_id INTEGER,
            service_id INTEGER,
            details TEXT,
            non_provided_services TEXT,
            is_24_hours INTEGER DEFAULT 0,
            start_time TEXT,
            end_time TEXT,
            working_days TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (service_provider_id) REFERENCES service_providers(user_id),
            FOREIGN KEY (service_id) REFERENCES main_services(id))''')

        # ساعات العمل
        c.execute('''CREATE TABLE IF NOT EXISTS service_working_hours (
    id INTEGER PRIMARY KEY,
    service_provider_service_id INTEGER,
    day TEXT,
    start_time TEXT,
    end_time TEXT,
    is_24_hours INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (service_provider_service_id) REFERENCES service_provider_services(id));''')

        # جدول المناطق التي يغطيها مقدم الخدمة
        c.execute('''CREATE TABLE IF NOT EXISTS service_areas (
            id INTEGER PRIMARY KEY,
            service_provider_service_id INTEGER,
            country_id INTEGER,
            district_id INTEGER,
            city_id INTEGER,
            is_all_districts INTEGER DEFAULT 0,
            is_all_cities INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (service_provider_service_id) REFERENCES service_provider_services(id),
            FOREIGN KEY (country_id) REFERENCES countries(id),
            FOREIGN KEY (district_id) REFERENCES districts(id),
            FOREIGN KEY (city_id) REFERENCES cities(id))''')

        # جدول end user
        c.execute('''CREATE TABLE IF NOT EXISTS end_users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            profile_picture TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id))''')

        # جدول admin
        c.execute('''CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            profile_picture TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id))''')

        # جدول التقييمات
        c.execute('''CREATE TABLE IF NOT EXISTS ratings
                  (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  provider_id INTEGER,
                  service_id INTEGER,
                  rating INTEGER,
                  comment TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  is_active INTEGER DEFAULT 1,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (provider_id) REFERENCES service_providers(user_id),
                  FOREIGN KEY (service_id) REFERENCES main_services(id))''')

       

        # تعديل الجدول الرئيسي
        c.execute('''CREATE TABLE IF NOT EXISTS service_providers_view
             (id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              phone TEXT,
              whatsapp TEXT,
              profile_picture TEXT,
              service_id INTEGER,
              service_name TEXT,
              service_details TEXT,
              non_provided_services TEXT,
              district_id INTEGER,
              city_id INTEGER,
              country_id INTEGER,
              district_name TEXT,
              city_name TEXT,
              country_name TEXT,
              average_rating REAL DEFAULT 0,
              is_active INTEGER DEFAULT 1,
              FOREIGN KEY (service_id) REFERENCES main_services(id),
              FOREIGN KEY (district_id) REFERENCES districts(id),
              FOREIGN KEY (city_id) REFERENCES cities(id),
              FOREIGN KEY (country_id) REFERENCES countries(id))''')

        


        # جدول جلسات الدردشة
        c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions
                     (id INTEGER PRIMARY KEY,
                      start_time TIMESTAMP,
                      end_time TIMESTAMP,
                      requested_service TEXT,
                      location TEXT,
                      recommended_providers TEXT)''')

        # جدول تفاصيل الدردشة
        c.execute('''CREATE TABLE IF NOT EXISTS chat_details
                     (id INTEGER PRIMARY KEY,
                      chat_session_id INTEGER,
                      timestamp TIMESTAMP,
                      user_input TEXT,
                      system_response TEXT,
                      input_tokens INTEGER,
                      output_tokens INTEGER,
                      FOREIGN KEY (chat_session_id) REFERENCES chat_sessions(id))''')

        # جدول إعدادات النموذج
        c.execute('''CREATE TABLE IF NOT EXISTS model_settings
                     (id INTEGER PRIMARY KEY,
                      model_name TEXT,
                      input_token_price REAL,
                      output_token_price REAL)''')

        # جدول الخدمات الرئيسية
        c.execute('''CREATE TABLE IF NOT EXISTS main_services
                     (id INTEGER PRIMARY KEY,
                      name TEXT UNIQUE,
                      is_active INTEGER DEFAULT 1)''')

        # جدول إصدارات البرومبت
        c.execute('''CREATE TABLE IF NOT EXISTS prompt_versions
                     (id INTEGER PRIMARY KEY,
                      content TEXT,
                      version_number INTEGER,
                      created_at TIMESTAMP,
                      is_active INTEGER,
                      comment TEXT)''')
        

        conn.commit()
        print("تم إنشاء قاعدة البيانات بنجاح")
    except sqlite3.Error as e:
        print(f"حدث خطأ أثناء إنشاء قاعدة البيانات: {e}", file=sys.stderr)
    finally:
        conn.close()

        




####server provider
def update_database_structure():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE service_providers ADD COLUMN profile_picture TEXT")
        print("تم إضافة عمود الصورة الشخصية بنجاح")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            print(f"خطأ في إضافة عمود الصورة الشخصية: {str(e)}")
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def get_service_providers():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    query = '''
    SELECT u.id, sp.name, u.email, u.phone, u.whatsapp, sp.profile_picture, u.is_active,
           GROUP_CONCAT(DISTINCT ms.name) AS services,
           GROUP_CONCAT(DISTINCT c.name) AS cities,
           AVG(r.rating) AS avg_rating,
           COUNT(DISTINCT r.id) AS rating_count
    FROM users u
    JOIN service_providers sp ON u.id = sp.user_id
    LEFT JOIN service_provider_services sps ON sp.user_id = sps.service_provider_id
    LEFT JOIN main_services ms ON sps.service_id = ms.id
    LEFT JOIN service_areas sa ON sps.id = sa.service_provider_service_id
    LEFT JOIN cities c ON sa.city_id = c.id
    LEFT JOIN ratings r ON sp.user_id = r.provider_id
    WHERE u.role = 'service_provider'
    GROUP BY u.id
    '''

    c.execute(query)
    providers = c.fetchall()
    conn.close()

    result = []
    for provider in providers:
        result.append({
            'id': provider[0],
            'name': provider[1],
            'email': provider[2],
            'phone': provider[3],
            'whatsapp': provider[4],
            'profile_picture': provider[5],
            'is_active': bool(provider[6]),
            'services': provider[7] if provider[7] else None,
            'cities': provider[8] if provider[8] else None,
            'avg_rating': provider[9] if provider[9] is not None else None,
            'rating_count': provider[10] or 0
        })

    return result
####استدعاء مقدم خدمة وحيد لاضافة الخدمات اليه
def get_service_provider(provider_id):
    """
    الحصول على معلومات مقدم خدمة محدد بواسطة provider_id.
    """
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        query = '''
        SELECT u.id, sp.name, u.phone, u.whatsapp, u.email, sp.profile_picture
        FROM users u
        JOIN service_providers sp ON u.id = sp.user_id
        WHERE u.role = 'service_provider' AND u.id = ?
        '''
        c.execute(query, (provider_id,))
        row = c.fetchone()
        if row:
            provider = {
                'id': row[0],
                'name': row[1],
                'phone': row[2],
                'whatsapp': row[3],
                'email': row[4],
                'profile_picture': row[5]
            }
            return provider
        else:
            return None
#####
####تفاصيل مقدم الخدمة والخدمات
def get_provider_details(provider_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT u.id, sp.name, u.email, u.phone, u.whatsapp, sp.profile_picture, u.is_active
        FROM users u
        JOIN service_providers sp ON u.id = sp.user_id
        WHERE u.id = ? AND u.role = 'service_provider'
    """, (provider_id,))
    basic_info = c.fetchone()

    if not basic_info:
        conn.close()
        return None

    provider = dict(basic_info)
    provider['services'] = []

    c.execute("""
        SELECT sps.id AS service_provider_service_id, ms.name AS service_name, sps.details, sps.non_provided_services
        FROM service_provider_services sps
        JOIN main_services ms ON sps.service_id = ms.id
        WHERE sps.service_provider_id = ?
    """, (provider_id,))
    services = c.fetchall()

    if services:
        for service in services:
            service_info = dict(service)
            service_info['details'] = service_info['details'].split(',') if service_info['details'] else []
            service_info['non_provided'] = service_info['non_provided_services'].split(',') if service_info['non_provided_services'] else []
            service_info['areas'] = {}
            service_info['working_hours'] = get_working_hours(service_info['service_provider_service_id'])

            c.execute("""
                SELECT sa.*, c.name AS country_name, ci.name AS city_name, d.name AS district_name
                FROM service_areas sa
                JOIN countries c ON sa.country_id = c.id
                LEFT JOIN cities ci ON sa.city_id = ci.id
                LEFT JOIN districts d ON sa.district_id = d.id
                WHERE sa.service_provider_service_id = ? AND sa.is_active = 1
            """, (service_info['service_provider_service_id'],))
            areas = c.fetchall()

            for area in areas:
                country = area['country_name']
                city = area['city_name'] if area['city_name'] else 'جميع المدن'

                if country not in service_info['areas']:
                    service_info['areas'][country] = {}

                if area['is_all_cities'] == 1:
                    service_info['areas'][country]['جميع المدن'] = ['جميع الأحياء']
                    continue

                if city not in service_info['areas'][country]:
                    service_info['areas'][country][city] = []

                if area['is_all_districts'] == 1:
                    service_info['areas'][country][city] = ['جميع الأحياء']
                elif area['district_name']:
                    service_info['areas'][country][city].append(area['district_name'])

            provider['services'].append(service_info)

    conn.close()
    return provider


#3
def get_active_main_services():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name FROM main_services WHERE is_active = 1")
    services = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
    conn.close()
    return services

def get_active_countries():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name FROM countries WHERE is_active = 1")
    countries = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
    conn.close()
    return countries

def get_active_cities(country_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name FROM cities WHERE country_id = ? AND is_active = 1", (country_id,))
    cities = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
    conn.close()
    return cities

def get_active_districts(city_ids):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    placeholders = ','.join('?' * len(city_ids))
    c.execute(f"SELECT id, name FROM districts WHERE city_id IN ({placeholders}) AND is_active = 1", city_ids)
    districts = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
    conn.close()
    return districts





def add_service_to_provider(provider_id, service_data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # إدراج الخدمة في جدول service_provider_services
        c.execute('''
            INSERT INTO service_provider_services (
                service_provider_id, service_id, service_details, non_provided_services, is_active
            ) VALUES (?, ?, ?, ?, 1)
        ''', (
            provider_id,
            service_data['service_id'],
            service_data['service_details'],
            service_data['non_provided_services']
        ))
        service_provider_service_id = c.lastrowid

        # معالجة المناطق وإدراجها في جدول service_areas
        for city_id in service_data['city_ids']:
            district_ids = service_data['districts'].get(city_id, [])
            if district_ids:
                for district_id in district_ids:
                    c.execute('''
                        INSERT INTO service_areas (
                            service_provider_service_id, city_id, district_id, is_active
                        ) VALUES (?, ?, ?, 1)
                    ''', (
                        service_provider_service_id,
                        city_id,
                        district_id
                    ))
            else:
                # إذا لم يتم اختيار أحياء، نضيف المدينة بدون تحديد حي
                c.execute('''
                    INSERT INTO service_areas (
                        service_provider_service_id, city_id, district_id, is_active
                    ) VALUES (?, ?, NULL, 1)
                ''', (
                    service_provider_service_id,
                    city_id
                ))

        # معالجة مواعيد العمل وإدراجها في جدول service_working_hours
        for day in service_data['working_days']:
            hours = service_data['working_hours'][day]
            if hours == '24_hours':
                c.execute('''
                    INSERT INTO service_working_hours (
                        service_provider_service_id, day, is_24_hours, is_active
                    ) VALUES (?, ?, 1, 1)
                ''', (
                    service_provider_service_id,
                    day
                ))
            else:
                for slot in hours:
                    c.execute('''
                        INSERT INTO service_working_hours (
                            service_provider_service_id, day, start_time, end_time, is_24_hours, is_active
                        ) VALUES (?, ?, ?, ?, 0, 1)
                    ''', (
                        service_provider_service_id,
                        day,
                        slot['start_time'],
                        slot['end_time']
                    ))

        conn.commit()
        print("تم إضافة الخدمة لمقدم الخدمة بنجاح")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"خطأ أثناء إضافة الخدمة لمقدم الخدمة: {e}")
        raise
    finally:
        conn.close()



######add services provider
def add_service_provider(name, phone, whatsapp, email, password, profile_picture=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        hashed_password = generate_password_hash(password)
        # إضافة المستخدم إلى جدول users
        c.execute('''INSERT INTO users 
                     (email, password_hash, phone, whatsapp, role, is_active)
                     VALUES (?, ?, ?, ?, 'service_provider', TRUE)''',
                  (email, hashed_password, phone, whatsapp))
        user_id = c.lastrowid

        # إضافة معلومات مقدم الخدمة إلى جدول service_providers
        c.execute('''INSERT INTO service_providers 
                     (user_id, name, profile_picture)
                     VALUES (?, ?, ?)''',
                  (user_id, name, profile_picture))

        conn.commit()
        print(f"Service provider added successfully with ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"Integrity Error in add_service_provider: {e}")
        if "UNIQUE constraint failed: users.email" in str(e):
            raise ValueError("البريد الإلكتروني مستخدم بالفعل")
        elif "UNIQUE constraint failed: users.whatsapp" in str(e):
            raise ValueError("رقم الواتساب مستخدم بالفعل")
        else:
            raise ValueError("خطأ في إدخال البيانات. الرجاء التحقق من المعلومات المدخلة.")
    except Exception as e:
        conn.rollback()
        print(f"Unexpected error in add_service_provider: {e}")
        raise ValueError("حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى لاحقًا.")
    finally:
        conn.close()
        # تشفير كلمة المرو

def check_phone_exists(phone):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE phone = ?", (phone,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def check_whatsapp_exists(whatsapp):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE whatsapp = ?", (whatsapp,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0
#4
def update_service_provider(provider_id, name, phone, whatsapp, email, profile_picture):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # التحقق من عدم وجود تعارض في البيانات
        c.execute('''
            SELECT COUNT(*) FROM users 
            WHERE (phone = ? OR whatsapp = ? OR email = ?) AND id != ?
        ''', (phone, whatsapp, email, provider_id))
        if c.fetchone()[0] > 0:
            raise ValueError("رقم الهاتف أو الواتساب أو البريد الإلكتروني مستخدم بالفعل")

        # تحديث البيانات في جدول users
        c.execute('''UPDATE users 
                     SET phone = ?, whatsapp = ?, email = ?
                     WHERE id = ?''',
                  (phone, whatsapp, email, provider_id))

        # تحديث البيانات في جدول service_providers
        c.execute('''UPDATE service_providers 
                     SET name = ?, profile_picture = ?
                     WHERE user_id = ?''',
                  (name, profile_picture, provider_id))

        conn.commit()
        print("تم تحديث مقدم الخدمة بنجاح")
    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"Integrity Error in update_service_provider: {e}")
        raise ValueError("خطأ في إدخال البيانات. الرجاء التحقق من المعلومات المدخلة.")
    except Exception as e:
        conn.rollback()
        print(f"Unexpected error in update_service_provider: {e}")
        raise ValueError("حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى لاحقًا.")
    finally:
        conn.close()


#5
def delete_service_provider(provider_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # جلب جميع service_provider_service_ids المرتبطة بمقدم الخدمة
        c.execute("SELECT id FROM service_provider_services WHERE service_provider_id = ?", (provider_id,))
        service_provider_service_ids = [row[0] for row in c.fetchall()]

        for sps_id in service_provider_service_ids:
            # حذف من service_working_hours
            c.execute("DELETE FROM service_working_hours WHERE service_provider_service_id = ?", (sps_id,))

            # حذف من service_areas
            c.execute("DELETE FROM service_areas WHERE service_provider_service_id = ?", (sps_id,))

        # حذف من service_provider_services
        c.execute("DELETE FROM service_provider_services WHERE service_provider_id = ?", (provider_id,))

        # حذف من service_providers
        c.execute("DELETE FROM service_providers WHERE user_id = ?", (provider_id,))

        # حذف من users
        c.execute("DELETE FROM users WHERE id = ? AND role = 'service_provider'", (provider_id,))

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

#6
def authenticate_provider(email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''SELECT u.id, sp.name, u.password_hash 
                     FROM users u
                     JOIN service_providers sp ON u.id = sp.user_id
                     WHERE u.email = ? AND u.role = 'service_provider' ''', (email,))
        result = c.fetchone()
        if result and check_password_hash(result[2], password):
            return result[0], result[1]  # return provider_id, name
    finally:
        conn.close()
    return None



import logging

logging.basicConfig(level=logging.DEBUG)

def toggle_provider_status(provider_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('UPDATE users SET is_active = NOT is_active WHERE id = ? AND role = "service_provider"', (provider_id,))
        conn.commit()
        c.execute('SELECT is_active FROM users WHERE id = ?', (provider_id,))
        new_status = c.fetchone()[0]
        return bool(new_status)
    except sqlite3.Error as e:
        print(f"Error toggling provider status: {e}")
        return None
    finally:
        conn.close()



def get_active_main_services():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name FROM main_services WHERE is_active = 1")
    services = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
    conn.close()
    return services

def check_email_exists(email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0


######end servier provider
#7
def add_user(username, email, password, phone=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        hashed_password = generate_password_hash(password)
        c.execute('''INSERT INTO users 
                     (email, password_hash, phone, role, is_active, created_at)
                     VALUES (?, ?, ?, 'end_user', TRUE, ?)''',
                  (email, hashed_password, phone, datetime.now()))
        user_id = c.lastrowid

        c.execute('INSERT INTO end_users (user_id, name) VALUES (?, ?)',
                  (user_id, username))

        conn.commit()
        return user_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"Integrity Error in add_user: {e}")
        raise ValueError("خطأ في إدخال البيانات. الرجاء التحقق من المعلومات المدخلة.")
    finally:
        conn.close()

#8
def authenticate_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''SELECT u.id, eu.name, u.password_hash 
                     FROM users u
                     JOIN end_users eu ON u.id = eu.user_id
                     WHERE u.email = ? AND u.role = 'end_user' ''', (email,))
        result = c.fetchone()
        if result and check_password_hash(result[2], password):
            return result[0], result[1]  # return user_id, username
    finally:
        conn.close()
    return None

#
def add_rating(user_id, provider_id, rating, comment):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''INSERT INTO ratings (user_id, provider_id, rating, comment)
                 VALUES (?, ?, ?, ?)''',
        (user_id, provider_id, rating, comment))
    conn.commit()

    # Update average rating
    c.execute(
        '''UPDATE service_providers_view
                 SET average_rating = (
                     SELECT AVG(rating) FROM ratings
                     WHERE provider_id = ?
                 )
                 WHERE id = ?''', (provider_id, provider_id))
    conn.commit()
    conn.close()


# ملف database.py

def get_ratings(provider_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT AVG(rating), COUNT(*) FROM ratings WHERE provider_id = ?''', (provider_id,))
    avg_rating, rating_count = c.fetchone()
    conn.close()
    return avg_rating, rating_count


#####
def get_city(city_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('SELECT id, name, country_id, is_active FROM cities WHERE id = ?', (city_id,))
        city = c.fetchone()
        if city:
            return {
                'id': city[0],
                'name': city[1],
                'country_id': city[2],
                'is_active': bool(city[3])
            }
        return None
    except sqlite3.Error as e:
        print(f"Error fetching city: {str(e)}", file=sys.stderr)
        return None
    finally:
        conn.close()

####الاحياء
def get_cities_by_country(country_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('SELECT id, name FROM cities WHERE country_id = ? AND is_active = 1', (country_id,))
        cities = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
        return cities
    except sqlite3.Error as e:
        print(f"Error fetching cities: {str(e)}", file=sys.stderr)
        return []
    finally:
        conn.close()

# ملف database.py

def get_districts_by_cities(city_ids):
    conn = get_db_connection()
    c = conn.cursor()
    placeholders = ','.join('?' * len(city_ids))
    c.execute(f"SELECT id, name, city_id FROM districts WHERE city_id IN ({placeholders}) AND is_active = 1", city_ids)
    districts = [{'id': row[0], 'name': row[1], 'city_id': row[2]} for row in c.fetchall()]
    conn.close()
    return districts



def get_districts(city_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, is_active FROM districts WHERE city_id = ?', (city_id,))
    districts = [{'id': row[0], 'name': row[1], 'is_active': bool(row[2])} for row in c.fetchall()]
    conn.close()
    return districts

# إضافة أو تحديث هذه الدوال في ملف database.py


def add_district(name, city_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO districts (name, city_id, is_active) VALUES (?, ?, 1)', (name, city_id))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding district: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

def update_district(district_id, new_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('UPDATE districts SET name = ? WHERE id = ?', (new_name, district_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating district: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def toggle_district_status(district_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('UPDATE districts SET is_active = NOT is_active WHERE id = ?', (district_id,))
        conn.commit()
        c.execute('SELECT is_active FROM districts WHERE id = ?', (district_id,))
        new_status = c.fetchone()[0]
        return bool(new_status)
    except sqlite3.Error as e:
        print(f"Error toggling district status: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

def delete_district(district_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('DELETE FROM districts WHERE id = ?', (district_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting district: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

######
###

def add_support_ticket(user_id, subject, message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''INSERT INTO customer_support_tickets (user_id, subject, message, status)
                 VALUES (?, ?, ?, 'Open')''', (user_id, subject, message))
    conn.commit()
    conn.close()


def get_support_tickets(user_id=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if user_id:
        c.execute(
            '''SELECT * FROM customer_support_tickets WHERE user_id = ?
                     ORDER BY created_at DESC''', (user_id, ))
    else:
        c.execute(
            'SELECT * FROM customer_support_tickets ORDER BY created_at DESC')
    tickets = c.fetchall()
    conn.close()
    return tickets


def update_support_ticket(ticket_id, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''UPDATE customer_support_tickets
                 SET status = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE id = ?''', (status, ticket_id))
    conn.commit()
    conn.close()


def save_prompt_version(content, version_number, comment):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''INSERT INTO prompt_versions (content, version_number, created_at, is_active, comment)
                 VALUES (?, ?, CURRENT_TIMESTAMP, 0, ?)''',
        (content, version_number, comment))
    conn.commit()
    conn.close()





def activate_prompt_version(version_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE prompt_versions SET is_active = 0')
    c.execute('UPDATE prompt_versions SET is_active = 1 WHERE id = ?',
              (version_id, ))
    conn.commit()
    conn.close()




def get_active_prompt():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(
            'SELECT content FROM prompt_versions WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1'
        )
        result = c.fetchone()
        return result[0] if result else None
    except sqlite3.OperationalError as e:
        print(f"Error in get_active_prompt: {e}", file=sys.stderr)
        print(
            "Trying to create prompt_versions table and insert default prompt",
            file=sys.stderr)
        create_database()  # This will create the table if it doesn't exist
        insert_default_prompt()
        # Try again after creating the table
        c.execute(
            'SELECT content FROM prompt_versions WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1'
        )
        result = c.fetchone()
        return result[0] if result else None
    finally:
        conn.close()


def get_prompt_history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM prompt_versions ORDER BY created_at DESC')
    history = c.fetchall()
    conn.close()
    return history


def start_chat_session(requested_service, location):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''INSERT INTO chat_sessions (start_time, requested_service, location)
                 VALUES (CURRENT_TIMESTAMP, ?, ?)''',
        (requested_service, location))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id


def end_chat_session(session_id, recommended_providers):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''UPDATE chat_sessions
                 SET end_time = CURRENT_TIMESTAMP, recommended_providers = ?
                 WHERE id = ?''',
        (','.join(map(str, recommended_providers)), session_id))
    conn.commit()
    conn.close()


def add_chat_detail(session_id, user_input, system_response, input_tokens,
                    output_tokens):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''INSERT INTO chat_details
                 (chat_session_id, timestamp, user_input, system_response, input_tokens, output_tokens)
                 VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
        (session_id, user_input, system_response, input_tokens, output_tokens))
    conn.commit()
    conn.close()


def get_model_settings():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM model_settings ORDER BY id DESC LIMIT 1')
    settings = c.fetchone()
    conn.close()
    return settings


def check_model_settings():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM model_settings ORDER BY id DESC LIMIT 1')
    settings = c.fetchone()
    conn.close()

    if settings is None:
        print(
            "تحذير: لم يتم العثور على إعدادات النموذج في قاعدة البيانات. يرجى إضافتها من خلال واجهة الإدارة.",
            file=sys.stderr)
    else:
        print(f"إعدادات النموذج الحالية: {settings}", file=sys.stderr)

    return settings is not None


def update_model_settings(model_name, input_token_price, output_token_price):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''INSERT OR REPLACE INTO model_settings (id, model_name, input_token_price, output_token_price)
                 VALUES (1, ?, ?, ?)''',
        (model_name, input_token_price, output_token_price))
    conn.commit()
    conn.close()

#جديد





#####services
#########


def add_main_service(name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO main_services (name) VALUES (?)', (name, ))
    conn.commit()
    conn.close()

def update_service(service_id, new_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('UPDATE main_services SET name = ? WHERE id = ?', (new_name, service_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating service: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def delete_service(service_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('DELETE FROM main_services WHERE id = ?', (service_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting service: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def toggle_service_status(service_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('UPDATE main_services SET is_active = NOT is_active WHERE id = ?', (service_id,))
        conn.commit()
        c.execute('SELECT is_active FROM main_services WHERE id = ?', (service_id,))
        new_status = c.fetchone()[0]
        return bool(new_status)
    except sqlite3.Error as e:
        print(f"Error toggling service status: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

# تحديث الدالة الموجودة لتشمل حالة التفعيل
def get_main_services():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, COALESCE(is_active, 1) as is_active FROM main_services')
    services = [{'id': row[0], 'name': row[1], 'is_active': bool(row[2])} for row in c.fetchall()]
    conn.close()
    return services



######end services
###########

def get_chat_statistics(start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''SELECT COUNT(DISTINCT cs.id) as session_count,
                            SUM(cd.input_tokens) as total_input_tokens,
                            SUM(cd.output_tokens) as total_output_tokens
                     FROM chat_sessions cs
                     JOIN chat_details cd ON cs.id = cd.chat_session_id
                     WHERE cs.start_time BETWEEN ? AND ?''',
        (start_date, end_date))
    stats = c.fetchone()
    conn.close()
    return stats


def create_database_backup():
    backup_file = 'sahl_new_backup.db'
    shutil.copyfile(DB_NAME, backup_file)
    print("تم إنشاء نسخة احتياطية من قاعدة البيانات")
    return backup_file


######back up
import shutil

shutil.copyfile('sahl_new.db', 'sahl_new_backup.db')
print("تم إنشاء نسخة احتياطية من قاعدة البيانات")



#الدول
def add_country(name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO countries (name) VALUES (?)', (name, ))
    conn.commit()
    conn.close()


def get_countries():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, is_active FROM countries')
    countries = [{
        'id': row[0],
        'name': row[1],
        'is_active': bool(row[2])
    } for row in c.fetchall()]
    conn.close()
    return countries


def update_country(country_id, new_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('UPDATE countries SET name = ? WHERE id = ?',
                  (new_name, country_id))
        conn.commit()
        print(
            f"تم تحديث الدولة بنجاح: ID {country_id}, الاسم الجديد: {new_name}",
            file=sys.stderr)
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"خطأ في تحديث الدولة: {str(e)}", file=sys.stderr)
        return False
    finally:
        conn.close()


def toggle_country_status(country_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(
            'UPDATE countries SET is_active = NOT is_active WHERE id = ?',
            (country_id, ))
        conn.commit()
        c.execute('SELECT is_active FROM countries WHERE id = ?',
                  (country_id, ))
        new_status = c.fetchone()[0]
        print(
            f"تم تغيير حالة الدولة: ID {country_id}, الحالة الجديدة: {'مفعلة' if new_status else 'معطلة'}",
            file=sys.stderr)
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"خطأ في تغيير حالة الدولة: {str(e)}", file=sys.stderr)
        return False
    finally:
        conn.close()

def get_country(country_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('SELECT id, name, is_active FROM countries WHERE id = ?', (country_id,))
        country = c.fetchone()
        if country:
            return {
                'id': country[0],
                'name': country[1],
                'is_active': bool(country[2])
            }
        return None
    except sqlite3.Error as e:
        print(f"Error fetching country: {str(e)}", file=sys.stderr)
        return None
    finally:
        conn.close()

#المدن



# ... (الدوال الأخرى تبقى كما هي)

def get_cities(country_id=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        if country_id:
            c.execute('SELECT id, name, is_active FROM cities WHERE country_id = ?', (country_id,))
            cities = [{'id': row[0], 'name': row[1], 'is_active': bool(row[2])} for row in c.fetchall()]
        else:
            c.execute('SELECT id, name, country_id, is_active FROM cities')
            cities = [{'id': row[0], 'name': row[1], 'country_id': row[2], 'is_active': bool(row[3])} for row in c.fetchall()]
        return cities
    except sqlite3.Error as e:
        print(f"Error fetching cities: {str(e)}", file=sys.stderr)
        return []
    finally:
        conn.close()

###
def add_city(name, country_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO cities (name, country_id, is_active) VALUES (?, ?, 1)', (name, country_id))
        conn.commit()
        return c.lastrowid  # يعيد معرف المدينة الجديدة
    except sqlite3.Error as e:
        print(f"Error adding city: {str(e)}", file=sys.stderr)
        return None
    finally:
        conn.close()
####
def get_city(city_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('SELECT id, name, country_id, is_active FROM cities WHERE id = ?', (city_id,))
        row = c.fetchone()
        if row:
            return {'id': row[0], 'name': row[1], 'country_id': row[2], 'is_active': row[3]}
        return None
    except sqlite3.Error as e:
        print(f"Error fetching city: {str(e)}", file=sys.stderr)
        return None
    finally:
        conn.close()

######
def get_city_by_name_and_country(city_name, country_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('SELECT id, name, is_active FROM cities WHERE name = ? AND country_id = ?', (city_name, country_id))
        row = c.fetchone()
        if row:
            return {'id': row[0], 'name': row[1], 'is_active': row[2]}
        return None
    except sqlite3.Error as e:
        print(f"Error fetching city: {str(e)}", file=sys.stderr)
        return None
    finally:
        conn.close()
######
def update_city(city_id, new_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('UPDATE cities SET name = ? WHERE id = ?', (new_name, city_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating city: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def toggle_city_status(city_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('UPDATE cities SET is_active = NOT is_active WHERE id = ?', (city_id,))
        conn.commit()
        c.execute('SELECT is_active FROM cities WHERE id = ?', (city_id,))
        new_status = c.fetchone()[0]
        return bool(new_status)
    except sqlite3.Error as e:
        print(f"Error toggling city status: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

def delete_city(city_id):
    conn = sqlite3.connect('sahl_new.db')
    c = conn.cursor()
    try:
        # قبل الحذف، تحقق من عدم وجود أحياء مرتبطة بالمدينة
        c.execute('SELECT COUNT(*) FROM districts WHERE city_id = ?', (city_id,))
        if c.fetchone()[0] > 0:
            print(f"Cannot delete city: ID {city_id}. It has associated districts.", file=sys.stderr)
            return False

        c.execute('DELETE FROM cities WHERE id = ?', (city_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error deleting city: {str(e)}", file=sys.stderr)
        return False
    finally:
        conn.close()


### نهاية المدن
def get_districts(city_id=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if city_id:
        c.execute('SELECT id, name, is_active FROM districts WHERE city_id = ?', (city_id,))
    else:
        c.execute('SELECT id, name, is_active FROM districts')
    districts = [{'id': row[0], 'name': row[1], 'is_active': bool(row[2])} for row in c.fetchall()]
    conn.close()
    return districts





def search_service_providers(service=None, city=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = "SELECT * FROM service_providers_view WHERE is_active = 1"
    params = []
    if service:
        query += " AND services LIKE ?"
        params.append(f'%{service}%')
    if city:
        query += " AND cities LIKE ?"
        params.append(f'%{city}%')
    c.execute(query, params)
    providers = [{
        'id': row[0],
        'name': row[1],
        'services': row[2],
        'cities': row[3],
        'districts': row[4],
        'phone': row[5],
        'whatsapp': row[6],
        'profile_picture': row[7],
        'service_details': row[8],
        'email': row[10],
        'average_rating': row[13]
    } for row in c.fetchall()]
    conn.close()
    return providers


def get_chat_session(session_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id, ))
    session = c.fetchone()
    conn.close()
    if session:
        return {
            'id': session[0],
            'start_time': session[1],
            'end_time': session[2],
            'requested_service': session[3],
            'location': session[4],
            'recommended_providers': session[5]
        }
    return None


def get_chat_details(session_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM chat_details WHERE chat_session_id = ? ORDER BY timestamp",
        (session_id, ))
    details = [{
        'id': row[0],
        'timestamp': row[2],
        'user_input': row[3],
        'system_response': row[4],
        'input_tokens': row[5],
        'output_tokens': row[6]
    } for row in c.fetchall()]
    conn.close()
    return details

def secure_filename(filename):
    """
    Return a secure version of the filename.
    """
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^\w\s.-]', '', filename.strip().lower())
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename
def insert_default_prompt():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    default_prompt = """
    أنت مساعد ذكي لشركة SAHL، متخصص في ربط المستخدمين بمقدمي الخدمات. اتبع هذه التعليمات بدقة:
    1. استخدم فقط المعلومات المتوفرة في {context}. لا تختلق أي معلومات إضافية.
    2. عند طلب خدمة، استجب بالصيغة التالية بالضبط:
       سعيد بمساعدتك. طلبت [الخدمة] في [المدينة]. 
       [إذا توفرت معلومات في {context}]:
       لدينا مقدمي الخدمة التاليين:
       [اسم] - [خدمات] - [مدن] - [هاتف]
       [كرر لكل مقدم خدمة متوفر]
       [إذا لم تتوفر معلومات]:
       عذرًا، لا تتوفر حاليًا معلومات عن [الخدمة] في [المدينة].
    3. كن مختصراً في ردودك. تجنب الإطالة أو إضافة معلومات غير ضرورية.
    4. إذا لم تتوفر معلومات محددة في {context}، لا تقدم أي افتراضات أو تخمينات.
    5. إذا كان السؤال غير مباشر أو غامض، اطلب توضيحاً قبل تقديم معلومات.
    6. اختم كل رد بسؤال مفتوح مثل "هل هناك شيء آخر يمكنني مساعدتك به؟"
    تاريخ المحادثة: {chat_history}
    سؤال العميل: {human_input}
    المعلومات المتاحة: {context}
    المساعد:
    """
    try:
        c.execute('SELECT COUNT(*) FROM prompt_versions')
        if c.fetchone()[0] == 0:
            c.execute(
                '''INSERT INTO prompt_versions (content, version_number, created_at, is_active, comment)
                         VALUES (?, 1, CURRENT_TIMESTAMP, 1, 'Default prompt')''',
                (default_prompt, ))
            conn.commit()
            print("تم إدراج البرومبت الافتراضي", file=sys.stderr)
    except sqlite3.OperationalError:
        print("جدول prompt_versions غير موجود. جاري إنشاؤه...",
              file=sys.stderr)
        c.execute('''CREATE TABLE IF NOT EXISTS prompt_versions
                     (id INTEGER PRIMARY KEY,
                      content TEXT,
                      version_number INTEGER,
                      created_at TIMESTAMP,
                      is_active BOOLEAN,
                      comment TEXT)''')
        c.execute(
            '''INSERT INTO prompt_versions (content, version_number, created_at, is_active, comment)
                     VALUES (?, 1, CURRENT_TIMESTAMP, 1, 'Default prompt')''',
            (default_prompt, ))
        conn.commit()
        print("تم إنشاء الجدول وإدراج البرومبت الافتراضي", file=sys.stderr)
    finally:
        conn.close()

def request_password_reset(provider_id):
    # توليد رمز إعادة التعيين
    reset_token = generate_reset_token()

    # إنشاء اتصال بقاعدة البيانات
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        # جلب البريد الإلكتروني لمقدم الخدمة
        c.execute('SELECT email FROM service_providers WHERE id = ?', (provider_id,))
        provider_email = c.fetchone()[0]

        # حفظ رمز إعادة التعيين في قاعدة البيانات
        c.execute('UPDATE service_providers SET reset_token = ? WHERE id = ?', (reset_token, provider_id))
        conn.commit()

        # إرسال رمز إعادة التعيين عبر البريد الإلكتروني
        send_reset_email(provider_email, reset_token)

    except Exception as e:
        print(f"حدث خطأ أثناء معالجة طلب إعادة التعيين: {e}")
    finally:
        # إغلاق الاتصال بقاعدة البيانات
        conn.close()

def get_districts_for_service(service_provider_service_id, city_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # الاستعلام لجلب الأحياء الخاصة بالخدمة المحددة والمدينة المحددة
        c.execute('''
            SELECT DISTINCT d.id, d.name
            FROM service_areas sa
            JOIN districts d ON sa.district_id = d.id
            WHERE sa.service_provider_service_id = ? 
              AND sa.city_id = ?
              AND sa.is_active = 1
              AND d.is_active = 1
        ''', (service_provider_service_id, city_id))
        
        districts = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
        
        return districts if districts else [{'id': None, 'name': 'لا توجد أحياء محددة'}]
    except sqlite3.Error as e:
        print(f"Error fetching districts for service: {str(e)}", file=sys.stderr)
        return [{'id': None, 'name': 'خطأ أثناء جلب الأحياء'}]
    finally:
        conn.close()


def get_working_hours(service_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT is_24_hours, start_time, end_time, working_days
            FROM service_working_hours
            WHERE service_provider_service_id = ?
        ''', (service_id,))
        hours = c.fetchall()
        
        print(f"Raw working hours data for service {service_id}: {hours}", file=sys.stderr)
        
        if not hours:
            return {'is_24_hours': False, 'schedules': []}
        
        is_24_hours = any(hour[0] for hour in hours)
        
        if is_24_hours:
            working_days = hours[0][3].split(',') if hours[0][3] else []
            return {'is_24_hours': True, 'working_days': working_days}
        
        schedules = []
        for _, start_time, end_time, working_days in hours:
            if start_time and end_time:
                schedules.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'days': working_days.split(',') if working_days else []
                })
        
        print(f"Processed working hours data: {{'is_24_hours': {is_24_hours}, 'schedules': {schedules}}}", file=sys.stderr)
        return {'is_24_hours': False, 'schedules': schedules}
    finally:
        conn.close()


def add_default_model_settings():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('SELECT COUNT(*) FROM model_settings')
        if c.fetchone()[0] == 0:
            c.execute('''
                INSERT INTO model_settings (model_name, input_token_price, output_token_price)
                VALUES (?, ?, ?)
            ''', ('default_model', 0.0001, 0.0002))
            conn.commit()
            print("تم إضافة إعدادات النموذج الافتراضية", file=sys.stderr)
        else:
            print("إعدادات النموذج موجودة بالفعل", file=sys.stderr)
    except sqlite3.Error as e:
        print(f"خطأ في إضافة إعدادات النموذج الافتراضية: {e}", file=sys.stderr)
    finally:
        conn.close()

import secrets

def generate_reset_token():
    return secrets.token_urlsafe(32)

def create_indexes():
    import sqlite3
    DB_NAME = 'sahl_new.db'  # تأكد من أن اسم قاعدة البيانات صحيح

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # فهرس على البريد الإلكتروني في جدول المستخدمين
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        # فهرس على رقم الهاتف في جدول المستخدمين
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)')
        
        # فهرس على رقم الواتساب في جدول المستخدمين
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_whatsapp ON users(whatsapp)')
        
        # فهرس على الدور في جدول المستخدمين
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        
        # فهرس على حالة التفعيل في جدول المستخدمين
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)')
        
        # فهرس على user_id في جدول مقدمي الخدمات
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_providers_user_id ON service_providers(user_id)')
        
        # فهرس على service_provider_id في جدول خدمات مقدمي الخدمات
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_provider_services_provider_id ON service_provider_services(service_provider_id)')
        
        # فهرس على service_id في جدول خدمات مقدمي الخدمات
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_provider_services_service_id ON service_provider_services(service_id)')
        
        # فهرس على service_provider_service_id في جدول مناطق الخدمة
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_areas_service_provider_service_id ON service_areas(service_provider_service_id)')
        
        # فهرس على city_id في جدول مناطق الخدمة
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_areas_city_id ON service_areas(city_id)')
        
        # فهرس على district_id في جدول مناطق الخدمة
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_areas_district_id ON service_areas(district_id)')
        
        # فهرس على country_id في جدول المدن
        c.execute('CREATE INDEX IF NOT EXISTS idx_cities_country_id ON cities(country_id)')
        
        # فهرس على city_id في جدول الأحياء
        c.execute('CREATE INDEX IF NOT EXISTS idx_districts_city_id ON districts(city_id)')
        
        # فهرس على provider_id في جدول التقييمات
        c.execute('CREATE INDEX IF NOT EXISTS idx_ratings_provider_id ON ratings(provider_id)')
        
        # فهرس على user_id في جدول التقييمات
        c.execute('CREATE INDEX IF NOT EXISTS idx_ratings_user_id ON ratings(user_id)')
        
        # فهرس على service_id في جدول التقييمات
        c.execute('CREATE INDEX IF NOT EXISTS idx_ratings_service_id ON ratings(service_id)')
        
        # فهرس على is_active في جدول الخدمات الرئيسية
        c.execute('CREATE INDEX IF NOT EXISTS idx_main_services_is_active ON main_services(is_active)')
        
        # فهرس على service_provider_service_id في جدول ساعات العمل
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_working_hours_service_provider_service_id ON service_working_hours(service_provider_service_id)')
        
        # فهرس على is_active في جدول مقدمي الخدمات
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_providers_is_active ON service_providers(user_id)')
        
        # فهرس على is_active في جدول خدمات مقدمي الخدمات
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_provider_services_is_active ON service_provider_services(is_active)')
        
        # فهرس على is_active في جدول مناطق الخدمة
        c.execute('CREATE INDEX IF NOT EXISTS idx_service_areas_is_active ON service_areas(is_active)')
        
        # فهرس على is_active في جدول المستخدمين النهائيين
        c.execute('CREATE INDEX IF NOT EXISTS idx_end_users_is_active ON end_users(user_id)')
        
        conn.commit()
        print("تم إنشاء جميع الفهارس بنجاح")
    except sqlite3.Error as e:
        print(f"حدث خطأ أثناء إنشاء الفهارس: {e}")
    finally:
        conn.close()

