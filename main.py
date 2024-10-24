from flask import Flask, render_template, render_template_string, request, jsonify, redirect, url_for, session, send_file, flash
import os
from werkzeug.utils import secure_filename
import sqlite3
import phonenumbers
import traceback
import sys
import re
from datetime import datetime
from chatbot import (process_user_input, update_prompt, start_new_chat_session,
                     end_current_chat_session, get_chat_cost)
from database import (add_default_model_settings, add_service_provider, check_whatsapp_exists, create_database, get_active_prompt, save_prompt_version, get_db_connection,
                      get_prompt_history, activate_prompt_version, update_database_structure,
                      get_service_providers, get_service_provider, add_service_to_provider, get_countries, update_country,
                      get_cities, add_city, update_city, toggle_city_status, 
                      delete_city, get_main_services, add_country, add_district, add_main_service,
                      update_service, delete_service, toggle_service_status, get_active_main_services,
                      update_district, delete_district,  toggle_district_status, get_districts_by_cities,
                      get_cities_by_country, get_city, get_provider_details, add_service_to_provider,
                      toggle_provider_status, delete_service_provider, update_model_settings,
                      get_chat_statistics, get_model_settings, create_database_backup, get_districts,
                      check_model_settings, toggle_country_status, get_country, check_email_exists,
                      check_phone_exists, get_active_countries, get_provider_details, get_districts_for_service, get_working_hours)
DB_NAME = 'sahl_new.db'


main = Flask(__name__)

main.secret_key = 'your_secret_key_here'  # تأكد من تغيير هذا في الإنتاج

UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

main.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_phone_number(phone, region):
    try:
        parsed_phone = phonenumbers.parse(phone, region)
        return phonenumbers.is_valid_number(parsed_phone)
    except phonenumbers.phonenumberutil.NumberParseException:
        return False

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json['message']
        print(f"Received user input: {user_input}", file=sys.stderr)

        if 'chat_session_id' not in session:
            requested_service = "خدمة افتراضية"
            location = "موقع افتراضي"
            session['chat_session_id'] = start_new_chat_session(requested_service, location)

        response, input_tokens, output_tokens = process_user_input(user_input, session['chat_session_id'])
        chat_cost = get_chat_cost(input_tokens, output_tokens)

        print(f"Response: {response}", file=sys.stderr)
        print(f"Chat cost: {chat_cost}", file=sys.stderr)

        return jsonify({'response': response, 'cost': chat_cost})
    except Exception as e:
        print(f"Error in chat: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': 'حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى.'}), 500

@main.route('/end_chat', methods=['POST'])
def end_chat():
    if 'chat_session_id' in session:
        end_current_chat_session(session['chat_session_id'])
        session.pop('chat_session_id', None)
    return jsonify({'message': 'تم إنهاء المحادثة بنجاح'})

@main.route('/admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@main.route('/admin/prompts', methods=['GET', 'POST'])
def admin_prompts():
    if request.method == 'POST':
        prompt = request.form['prompt']
        comment = request.form['comment']
        version_number = int(request.form['version_number'])
        save_prompt_version(prompt, version_number, comment)
        update_prompt()
        return redirect(url_for('admin_prompts'))
    active_prompt = get_active_prompt()
    prompt_history = get_prompt_history()
    return render_template('admin_prompts.html', active_prompt=active_prompt, prompt_history=prompt_history)

@main.route('/admin/activate_prompt/<int:version_id>', methods=['POST'])
def admin_activate_prompt(version_id):
    activate_prompt_version(version_id)
    update_prompt()
    return redirect(url_for('admin_prompts'))


#####add provider
@main.route('/admin/add_provider', methods=['POST'])
def add_provider():
    print("Received data:", request.form)  # طباعة البيانات المستلمة
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        whatsapp = request.form.get('whatsapp')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([name, phone, whatsapp, email, password, confirm_password]):
            return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'})

        if password != confirm_password:
            return jsonify({'success': False, 'message': 'كلمتا المرور غير متطابقتين'})

        if not validate_phone_number(phone, 'EG') or not validate_phone_number(whatsapp, 'EG'):
            return jsonify({'success': False, 'message': 'رقم الهاتف أو الواتساب غير صالح'})

        if check_email_exists(email):
            return jsonify({'success': False, 'message': 'البريد الإلكتروني مستخدم بالفعل'})

        if check_phone_exists(phone):
            return jsonify({'success': False, 'message': 'رقم الهاتف مستخدم بالفعل'})

        if check_whatsapp_exists(whatsapp):
            return jsonify({'success': False, 'message': 'رقم الواتساب مستخدم بالفعل'})

        filename = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(main.config['UPLOAD_FOLDER'], filename))

        provider_id = add_service_provider(name, phone, whatsapp, email, password, filename)

        return jsonify({"success": True, "message": "تمت إضافة مقدم الخدمة بنجاح", "provider_id": provider_id})

    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)})

    except Exception as e:
        print(f"Error in add_provider: {str(e)}")
        return jsonify({"success": False, "message": "حدث خطأ أثناء إضافة مقدم الخدمة. الرجاء المحاولة مرة أخرى."})




@main.route('/admin/provider_details/<int:provider_id>')
def provider_details(provider_id):
    provider = get_provider_details(provider_id)
    if 'services' not in provider:
        # إذا لم يكن هناك خدمات، نعيد صفحة خطأ أو رسالة مناسبة
        return "لا توجد خدمات لهذا المزود", 404
    
    for service in provider['services']:
        if 'id' not in service or 'city_id' not in service:
            # إذا كانت البيانات ناقصة، نتخطى هذه الخدمة
            continue
        service['districts'] = get_districts_for_service(service['id'], service['city_id'])
        service['working_hours'] = get_working_hours(service['id'])
    
    return render_template('provider_details.html', provider=provider)


#######update provider
@main.route('/admin/update_provider', methods=['POST'])
def update_provider():
    provider_id = request.form.get('provider_id')
    name = request.form.get('name')
    phone = request.form.get('phone')
    whatsapp = request.form.get('whatsapp')
    email = request.form.get('email')

    # التحقق من وجود صورة جديدة
    if 'profile_picture' in request.files and request.files['profile_picture'].filename != '':
        file = request.files['profile_picture']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(main.config['UPLOAD_FOLDER'], filename))
            profile_picture = filename
        else:
            return jsonify({"success": False, "message": "نوع الملف غير مدعوم!"})
    else:
        profile_picture = None

    try:
        # تحديث البيانات في جدول users
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
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
        conn.close()
        return jsonify({"success": True, "message": "تم تعديل البيانات بنجاح"})
    except sqlite3.IntegrityError as e:
        return jsonify({"success": False, "message": "البيانات المدخلة موجودة بالفعل لمستخدم آخر"})
    except Exception as e:
        print(f"Error updating provider: {str(e)}")
        return jsonify({"success": False, "message": "حدث خطأ أثناء تحديث البيانات"})

@main.route('/admin/service_providers')
def admin_service_providers():
    providers = get_service_providers()
    return render_template('admin_service_providers.html', providers=providers)
######
from flask import Flask, render_template, request, redirect, url_for, flash
from database import (
    get_active_main_services,
    get_active_countries,
    get_service_provider,
    add_service_to_provider
)





@main.route('/admin/add_service/<int:provider_id>', methods=['GET', 'POST'])
def admin_add_service(provider_id):
    if request.method == 'POST':
        try:
            # جمع مؤشرات الخدمات من أسماء الحقول
            service_indices = set()
            for key in request.form.keys():
                match = re.match(r'services\[(\d+)\]\[.*\]', key)
                if match:
                    service_indices.add(match.group(1))

            print('Service indices:', service_indices)

            for index in service_indices:
                service_id = request.form.get(f'services[{index}][service_id]')
                service_details = request.form.get(f'services[{index}][service_details]')
                non_provided_services = request.form.get(f'services[{index}][non_provided_services]')
                country_id = request.form.get(f'services[{index}][country_id]')
                city_ids = request.form.getlist(f'services[{index}][city_ids][]')
                districts = {}
                for city_id in city_ids:
                    district_ids = request.form.getlist(f'services[{index}][districts][{city_id}][]')
                    districts[city_id] = district_ids
                working_days = request.form.getlist(f'services[{index}][working_days][]')
                working_hours = {}
                for day in working_days:
                    hours_type = request.form.get(f'services[{index}][hours_type][{day}]')
                    if hours_type == '24_hours':
                        working_hours[day] = '24_hours'
                    else:
                        start_times = request.form.getlist(f'services[{index}][working_hours][{day}][start_times][]')
                        end_times = request.form.getlist(f'services[{index}][working_hours][{day}][end_times][]')
                        time_slots = []
                        for start_time, end_time in zip(start_times, end_times):
                            time_slots.append({'start_time': start_time, 'end_time': end_time})
                        working_hours[day] = time_slots

                service_data = {
                    'service_id': service_id,
                    'service_details': service_details,
                    'non_provided_services': non_provided_services,
                    'country_id': country_id,
                    'city_ids': city_ids,
                    'districts': districts,
                    'working_days': working_days,
                    'working_hours': working_hours
                }

                # استدعاء الدالة لإضافة الخدمة إلى مقدم الخدمة
                add_service_to_provider(provider_id, service_data)

            flash('تم إضافة الخدمات بنجاح', 'success')
            return redirect(url_for('admin_service_providers'))
        except Exception as e:
            flash(f'حدث خطأ أثناء إضافة الخدمات: {e}', 'danger')
            print(f'Exception occurred: {e}')
            return redirect(url_for('admin_add_service', provider_id=provider_id))
    else:
        # معالجة طلب GET
        services = get_active_main_services()
        countries = get_active_countries()
        provider = get_service_provider(provider_id)
        if not provider:
            flash('مقدم الخدمة غير موجود', 'danger')
            return redirect(url_for('admin_service_providers'))
        return render_template('admin_add_service.html', services=services, countries=countries, provider=provider)

#######

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn
######
from database import toggle_provider_status as db_toggle_provider_status
from database import delete_service_provider as db_delete_service_provider


@main.route('/admin/toggle_provider_status/<int:provider_id>', methods=['POST'])
def toggle_provider_status(provider_id):
    print(f"Attempting to toggle status for provider {provider_id}")
    try:
        new_status = db_toggle_provider_status(provider_id)
        success = True
        message = f"تم تغيير الحالة بنجاح. الحالة الجديدة: {'مفعل' if new_status else 'معطل'}"
    except Exception as e:
        print(f"Error toggling provider status: {str(e)}")
        success = False
        message = "فشل في تغيير الحالة"
    return jsonify({'success': success, 'message': message})




@main.route('/admin/delete_provider/<int:provider_id>', methods=['POST'])
def delete_provider(provider_id):
    print(f"Attempting to delete provider {provider_id}")
    try:
        result = delete_service_provider(provider_id)
        if result:
            success = True
            message = "تم حذف مقدم الخدمة بنجاح"
        else:
            success = False
            message = "فشل في حذف مقدم الخدمة"
    except Exception as e:
        print(f"Error deleting provider: {str(e)}")
        success = False
        message = f"حدث خطأ أثناء حذف مقدم الخدمة: {str(e)}"
    return jsonify({'success': success, 'message': message})
########

"""@main.route('/admin/toggle_provider_status/<int:provider_id>', methods=['POST'])
def toggle_provider_status(provider_id):
    conn = get_db_connection()
    c = conn.cursor()

    # تحقق من الحالة الحالية
    c.execute('SELECT is_active FROM service_providers WHERE id = ?', (provider_id,))
    current_status = c.fetchone()[0]

    # قلب الحالة الحالية
    new_status = 1 if current_status == 0 else 0

    # تحديث الحالة في قاعدة البيانات
    c.execute('UPDATE service_providers SET is_active = ? WHERE id = ?', (new_status, provider_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True})"""




@main.route('/admin/countries', methods=['GET', 'POST'])
def admin_countries():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            country_name = request.form.get('country_name')
            if country_name:
                if add_country(country_name):
                    flash('تمت إضافة الدولة بنجاح', 'success')
                else:
                    flash('فشل في إضافة الدولة', 'error')
            else:
                flash('الرجاء إدخال اسم الدولة', 'error')

        elif action == 'update':
            country_id = request.form.get('country_id')
            new_name = request.form.get('country_name')
            if country_id and new_name:
                if update_country(country_id, new_name):
                    flash('تم تحديث الدولة بنجاح', 'success')
                else:
                    flash('فشل في تحديث الدولة', 'error')
            else:
                flash('بيانات غير صالحة للتحديث', 'error')

        elif action == 'toggle_status':
            country_id = request.form.get('country_id')
            if country_id:
                if toggle_country_status(country_id):
                    flash('تم تغيير حالة الدولة بنجاح', 'success')
                else:
                    flash('فشل في تغيير حالة الدولة', 'error')
            else:
                flash('لم يتم تحديد الدولة', 'error')

        elif action == 'delete':
            country_id = request.form.get('country_id')
            if country_id:
                if delete_country(country_id): # type: ignore
                    flash('تم حذف الدولة بنجاح', 'success')
                else:
                    flash('فشل في حذف الدولة', 'error')
            else:
                flash('لم يتم تحديد الدولة للحذف', 'error')

        return redirect(url_for('admin_countries'))

    countries = get_countries()
    return render_template('admin_countries.html', countries=countries)

@main.route('/admin/countries/<int:country_id>/cities', methods=['GET', 'POST'])
def admin_cities_for_country(country_id):
    country = get_country(country_id)
    if not country:
        return jsonify({'success': False, 'message': 'الدولة غير موجودة'}), 404

    if request.method == 'POST':
        city_name = request.form.get('city_name')
        if city_name:
            new_city_id = add_city(city_name, country_id)
            if new_city_id:
                new_city = get_city(new_city_id)
                return jsonify({'success': True, 'message': 'تمت إضافة المدينة بنجاح', 'city': new_city})
            else:
                return jsonify({'success': False, 'message': 'فشل في إضافة المدينة'})
        else:
            return jsonify({'success': False, 'message': 'الرجاء إدخال اسم المدينة'})

    cities = get_cities(country_id)
    return render_template('admin_cities_for_country.html', country=country, cities=cities)

#####


@main.route('/get_districts_by_cities', methods=['POST'])
def get_districts_by_cities_route():
    city_ids = request.json.get('city_ids', [])
    districts = get_districts_by_cities(city_ids)
    result = {}
    for district in districts:
        city_id = str(district['city_id'])
        if city_id not in result:
            result[city_id] = []
        result[city_id].append({'id': district['id'], 'name': district['name']})
    print("Districts returned:", result)  # للتصحيح
    return jsonify(result)



#####
@main.route('/admin/cities', methods=['GET', 'POST'])
def admin_cities():
    if request.method == 'POST':
        action = request.form.get('action')
        country_id = request.form.get('country_id')

        if action == 'add':
            city_name = request.form.get('city_name')
            if city_name and country_id:
                success = add_city(city_name, int(country_id))
                if success:
                    flash('تمت إضافة المدينة بنجاح', 'success')
                else:
                    flash('فشل في إضافة المدينة', 'error')
            else:
                flash('الرجاء إدخال اسم المدينة واختيار الدولة', 'error')
        
        elif action == 'update':
            city_id = request.form.get('city_id')
            new_name = request.form.get('city_name')
            if city_id and new_name:
                success = update_city(city_id, new_name)
                if success:
                    flash('تم تحديث المدينة بنجاح', 'success')
                else:
                    flash('فشل في تحديث المدينة', 'error')
            else:
                flash('بيانات غير صالحة للتحديث', 'error')

        elif action == 'toggle_status':
            city_id = request.form.get('city_id')
            if city_id:
                new_status = toggle_city_status(city_id)
                if new_status is not None:
                    flash(f'تم تغيير حالة المدينة بنجاح. الحالة الجديدة: {"مفعلة" if new_status else "معطلة"}', 'success')
                else:
                    flash('فشل في تغيير حالة المدينة', 'error')
            else:
                flash('لم يتم تحديد المدينة', 'error')

        elif action == 'delete':
            city_id = request.form.get('city_id')
            if city_id:
                success = delete_city(city_id)
                if success:
                    flash('تم حذف المدينة بنجاح', 'success')
                else:
                    flash('فشل في حذف المدينة', 'error')
            else:
                flash('لم يتم تحديد المدينة للحذف', 'error')

        return redirect(url_for('admin_cities_for_country', country_id=country_id))

    countries = get_countries()
    return render_template('admin_cities.html', countries=countries)

@main.route('/admin/districts', methods=['GET', 'POST'])
def admin_districts():
    if request.method == 'POST':
        action = request.form.get('action')
        city_id = request.form.get('city_id')

        if action == 'add':
            district_name = request.form.get('district_name')
            if district_name and city_id:
                success = add_district(district_name, city_id)
                return jsonify({'success': success})
            return jsonify({'success': False})

        elif action == 'update':
            district_id = request.form.get('district_id')
            new_name = request.form.get('district_name')
            if district_id and new_name:
                success = update_district(district_id, new_name)
                return jsonify({'success': success})
            return jsonify({'success': False})

        elif action == 'toggle_status':
            district_id = request.form.get('district_id')
            if district_id:
                new_status = toggle_district_status(district_id)
                return jsonify({'success': True, 'new_status': new_status})
            return jsonify({'success': False})

        elif action == 'delete':
            district_id = request.form.get('district_id')
            if district_id:
                success = delete_district(district_id)
                return jsonify({'success': success})
            return jsonify({'success': False})

    countries = get_countries()
    return render_template('admin_districts.html', countries=countries)

@main.route('/get_cities_by_country/<int:country_id>')
def get_cities_by_country_route(country_id):
    print(f"Fetching cities for country_id: {country_id}")
    cities = get_cities_by_country(country_id)
    print(f"Cities fetched: {cities}")  # تأكد من أن هذه البيانات صحيحة
    return jsonify(cities)



@main.route('/admin/cities/<int:city_id>/districts', methods=['GET', 'POST'])
def admin_districts_for_city(city_id):
    city = get_city(city_id)
    if not city:
        flash('المدينة غير موجودة', 'error')
        return redirect(url_for('admin_cities_for_country', country_id=city.country_id))

    districts = get_districts(city_id)

    if request.method == 'POST':
        # تنفيذ عمليات إضافة أو تعديل أو حذف الأحياء
        pass

    return render_template('admin_districts_for_city.html', city=city, districts=districts)

@main.route('/admin/services', methods=['GET', 'POST'])
def admin_services():
    if request.method == 'POST':
        service_name = request.form['service_name']
        try:
            add_main_service(service_name)
            flash('تمت إضافة الخدمة بنجاح', 'success')
        except Exception as e:
            flash(f'حدث خطأ أثناء إضافة الخدمة: {str(e)}', 'error')
            print(f"Error adding service: {str(e)}", file=sys.stderr)
        return redirect(url_for('admin_services'))

    services = get_main_services()
    return render_template('admin_services.html', services=services)

@main.route('/admin/services/<int:id>/edit', methods=['POST'])
def edit_service(id):
    new_name = request.json.get('name')
    success = update_service(id, new_name)
    return jsonify({'success': success})

@main.route('/admin/services/<int:id>/delete', methods=['POST'])
def delete_service_route(id):
    success = delete_service(id)
    return jsonify({'success': success})

@main.route('/admin/services/<int:id>/toggle', methods=['POST'])
def toggle_service(id):
    success = toggle_service_status(id)
    return jsonify({'success': success})

@main.route('/admin/model_settings', methods=['GET', 'POST'])
def admin_model_settings():
    if request.method == 'POST':
        model_name = request.form['model_name']
        input_token_price = float(request.form['input_token_price'])
        output_token_price = float(request.form['output_token_price'])
        try:
            update_model_settings(model_name, input_token_price, output_token_price)
            flash('تم تحديث إعدادات النموذج بنجاح', 'success')
        except Exception as e:
            flash(f'حدث خطأ أثناء تحديث إعدادات النموذج: {str(e)}', 'error')
            print(f"Error updating model settings: {str(e)}", file=sys.stderr)
        return redirect(url_for('admin_model_settings'))

    current_settings = get_model_settings()
    return render_template('admin_model_settings.html', settings=current_settings)

@main.route('/admin/chat_statistics')
def admin_chat_statistics():
    start_date = request.args.get('start_date', default=datetime.now().date().isoformat())
    end_date = request.args.get('end_date', default=datetime.now().date().isoformat())
    stats = get_chat_statistics(start_date, end_date)
    return render_template('admin_chat_statistics.html', stats=stats)

@main.route('/admin/backup')
def backup_database():
    try:
        backup_file = create_database_backup()
        flash('تم إنشاء النسخة الاحتياطية بنجاح', 'success')
        return send_file(backup_file, as_attachment=True, download_name='sahl_backup.sql')
    except Exception as e:
        flash(f'حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}', 'error')
        print(f"Error creating backup: {str(e)}", file=sys.stderr)
        return redirect(url_for('admin_dashboard'))

@main.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@main.route('/admin/cities/<int:city_id>/update', methods=['POST'])
def update_city_route(city_id):
    new_name = request.form.get('city_name')
    success = update_city(city_id, new_name)
    return jsonify({'success': success})

@main.route('/admin/cities/<int:city_id>/toggle_status', methods=['POST'])
def toggle_city_status_route(city_id):
    new_status = toggle_city_status(city_id)
    return jsonify({'success': new_status is not None, 'new_status': new_status})

@main.route('/admin/districts/add', methods=['POST'])
def add_district_route():
    name = request.form.get('district_name')
    city_id = request.form.get('city_id')
    new_id = add_district(name, city_id)
    return jsonify({'success': new_id is not None, 'new_id': new_id})

@main.route('/admin/districts/<int:district_id>/update', methods=['POST'])
def update_district_route(district_id):
    new_name = request.form.get('district_name')
    success = update_district(district_id, new_name)
    return jsonify({'success': success})

@main.route('/admin/districts/<int:district_id>/toggle_status', methods=['POST'])
def toggle_district_status_route(district_id):
    new_status = toggle_district_status(district_id)
    return jsonify({'success': new_status is not None, 'new_status': new_status})

@main.route('/admin/districts/<int:district_id>/delete', methods=['POST'])
def delete_district_route(district_id):
    success = delete_district(district_id)
    return jsonify({'success': success})

#####اعادة تعيين كلمة السر

@main.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        # عرض صفحة إعادة تعيين كلمة المرور إذا كان الرمز صحيحًا
        token = request.args.get('token')
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('SELECT id FROM service_providers WHERE reset_token = ?', (token,))
            provider = c.fetchone()
            if provider:
                return render_template_string(open('reset_password.html').read(), reset_token=token)
            else:
                return "رابط غير صالح أو منتهي الصلاحية", 400

    elif request.method == 'POST':
        # معالجة طلب إعادة تعيين كلمة المرور
        reset_token = request.form['reset_token']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return "كلمتا المرور غير متطابقتين", 400

        # تحديث كلمة المرور الجديدة
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('UPDATE service_providers SET password = ?, reset_token = NULL WHERE reset_token = ?', (new_password, reset_token))
            conn.commit()

        return "تم إعادة تعيين كلمة المرور بنجاح"
    
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_reset_email(user_email, reset_link):
    # إعدادات البريد الإلكتروني الخاصة بـ Gmail
    sender_email = "may.pharmatrone@gmail.com"
    sender_password = "ocxx tbnj nklj mxjo"   # ملاحظة: عدل هذا ليكون البريد الإلكتروني الخاص بك
      # ملاحظة: عدل هذا ليكون كلمة مرور حساب Gmail الخاص بك أو كلمة المرور الخاصة بالتطبيق (App Password)
    
    receiver_email = user_email

    # إعداد الرسالة
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "إعادة تعيين كلمة المرور"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # محتوى البريد
    text = f"لإعادة تعيين كلمة المرور، يرجى زيارة الرابط التالي: {reset_link}"
    html = f"""
    <html>
    <body>
        <p>لإعادة تعيين كلمة المرور، يرجى زيارة الرابط التالي:</p>
        <a href="{reset_link}">إعادة تعيين كلمة المرور</a>
    </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    msg.attach(part1)
    msg.attach(part2)

    # إرسال البريد باستخدام SMTP
    try:
        # الاتصال بـ Gmail باستخدام SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:  # ملاحظة: إذا كنت تستخدم خدمة بريد أخرى، عدل العنوان والمنفذ هنا
            server.login(sender_email, sender_password)  # تسجيل الدخول إلى Gmail
            server.sendmail(sender_email, receiver_email, msg.as_string())  # إرسال البريد
            print("تم إرسال البريد الإلكتروني بنجاح")
    except Exception as e:
        print(f"فشل في إرسال البريد الإلكتروني: {e}")



if __name__ == '__main__':
    print("Starting application...", file=sys.stderr)
    create_database()
    print("Database created", file=sys.stderr)
    update_database_structure()
    add_default_model_settings()  # أضف هذا السطر
    
    if check_model_settings():
        print("Model settings found", file=sys.stderr)
    else:
        print("Please add model settings through the admin interface", file=sys.stderr)
    update_prompt()
    print("Prompt updated", file=sys.stderr)
    main.run(host='0.0.0.0', port=8080, debug=True)