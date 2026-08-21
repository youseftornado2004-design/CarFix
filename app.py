import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# مجلد حفظ الصور المرفوعة
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('StoreDB.db')
    conn.row_factory = sqlite3.Row
    return conn

# دالة التأكد من إنشاء جدول الزيوت أوتوماتيكياً بأمان تام
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS oils (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductName TEXT,
            Description TEXT,
            Price REAL,
            CarModel TEXT,
            Image TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect(url_for('select_car_page'))

@app.route('/select-car')
def select_car_page():
    return render_template('Select-Car.html')

# مسار استقبال وتخزين اختيار السيارة وتحويل العميل لصفحة المنتجات والزيوت
@app.route('/add_car', methods=['POST'])
def add_car():
    car_model = request.form.get('car_model') or request.form.get('model_name') or request.form.get('car_name')
    car_year = request.form.get('car_year') or request.form.get('year')
    
    # حفظ اختيار السيارة في الجلسة (Session) لتظهر في واجهة المنتجات
    session['car_model'] = car_model
    session['car_year'] = car_year
    
    return redirect(url_for('products_page'))

# مسار عرض المنتجات والزيوت معاً (مُتطابق مع اسم الملف Product.html عندك)
@app.route('/products')
def products_page():
    conn = get_db_connection()
    init_db()
    
    # جلب قطع الغيار بأمان
    try:
        products = conn.execute('SELECT * FROM products').fetchall()
    except:
        products = []
        
    # جلب الزيوت المضافة من لوحة التحكم
    oils = conn.execute('SELECT * FROM oils').fetchall()
    conn.close()
    
    car_model = session.get('car_model')
    car_year = session.get('car_year')
    
    return render_template('Product.html', products=products, oils=oils, car_model=car_model, car_year=car_year)

# صفحة عرض الزيوت المستقلة (لو احتجتها)
@app.route('/oils')
def oils_page():
    conn = get_db_connection()
    init_db()
    oils = conn.execute('SELECT * FROM oils').fetchall()
    conn.close()
    return render_template('Oils.html', oils=oils)

# لوحة تحكم الأدمن
@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    init_db()
    try:
        products = conn.execute('SELECT * FROM products').fetchall()
    except:
        products = []
        
    oils = conn.execute('SELECT * FROM oils').fetchall()
    conn.close()
    return render_template('Admin-Dashboard.html', products=products, oils=oils)

# معالجة إضافة زيت جديد من لوحة التحكم
@app.route('/add_oil', methods=['POST'])
def add_oil():
    product_name = request.form.get('product_name')
    description = request.form.get('description')
    price = request.form.get('price')
    car_model = request.form.get('car_model')
    
    image_file = request.files.get('image')
    image_filename = None
    if image_file and image_file.filename != '':
        image_filename = image_file.filename
        image_file.save(os.path.join(UPLOAD_FOLDER, image_filename))
    
    conn = get_db_connection()
    init_db()
    conn.execute('''
        INSERT INTO oils (ProductName, Description, Price, CarModel, Image)
        VALUES (?, ?, ?, ?, ?)
    ''', (product_name, description, price, car_model, image_filename))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

# مسار حفظ الشراء الوهمي لتجنب أخطاء المتصفح
@app.route('/save-purchase', methods=['POST'])
def save_purchase():
    return jsonify({'status': 'success'})

# صفحة بوليصة الشراء وتأكيد الطلب
@app.route('/order-confirmation')
def order_confirmation():
    return render_template('OrderConfirmation.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
