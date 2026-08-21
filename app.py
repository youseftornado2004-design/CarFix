import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# مجلد حفظ الصور المرفوعة
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('StoreDB.db')
    conn.row_factory = sqlite3.Row
    return conn

# دالة التأكد من إنشاء جدول الزيوت أوتوماتيكياً من غير المساس بجداول الداتا بيز الأخرى
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

# تشغيل فحص/إنشاء الجدول عند بدء التشغيل
init_db()

@app.route('/')
def home():
    return redirect(url_for('select_car_page'))

@app.route('/select-car')
def select_car_page():
    return render_template('Select-Car.html')

# صفحة عرض الزيوت
@app.route('/oils')
def oils_page():
    conn = get_db_connection()
    init_db()
    oils = conn.execute('SELECT * FROM oils').fetchall()
    conn.close()
    return render_template('Oils.html', oils=oils)

# لوحة تحكم الأدمن (بدون أي تأثير على جداول قطع الغيار أو السيارات القديمة)
@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    init_db()
    
    # جلب المنتجات القديمة لو وجدت بأمان تام
    try:
        products = conn.execute('SELECT * FROM products').fetchall()
    except:
        products = []
        
    oils = conn.execute('SELECT * FROM oils').fetchall()
    conn.close()
    return render_template('Admin-Dashboard.html', products=products, oils=oils)

# معالجة إضافة زيت جديد من لوحة التحكم وحفظه في الداتا بيز
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

# صفحة بوليصة الشراء وتأكيد الطلب
@app.route('/order-confirmation')
def order_confirmation():
    return render_template('OrderConfirmation.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
