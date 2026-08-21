import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# التأكد من وجود مجلد الرفع للصور
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# دالة للاتصال بقاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect('StoreDB.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return redirect(url_for('select_car_page'))

@app.route('/select-car')
def select_car_page():
    return render_template('Select-Car.html')

# مسار صفحة الزيوت (يعرض الزيوت المضافة من الداتا بيز)
@app.route('/oils')
def oils_page():
    conn = get_db_connection()
    oils = conn.execute('SELECT * FROM oils').fetchall()
    conn.close()
    return render_template('Oils.html', oils=oils)

# مسار لوحة التحكم للأدمن
@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    oils = conn.execute('SELECT * FROM oils').fetchall()
    conn.close()
    return render_template('Admin-Dashboard.html', products=products, oils=oils)

# مسار إضافة زيت جديد من لوحة التحكم (واقعي 100% للعميل)
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
    # لو جدول oils مش موجود، الكود بينشئه تلقائي عشان مفيش داتا بيز تبوظ
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
    conn.execute('''
        INSERT INTO oils (ProductName, Description, Price, CarModel, Image)
        VALUES (?, ?, ?, ?, ?)
    ''', (product_name, description, price, car_model, image_filename))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

# مسار صفحة تأكيد الطلب وبوليصة الشراء
@app.route('/order-confirmation')
def order_confirmation():
    # تقدر تستقبل بيانات الطلب هنا أو تعرض آخر طلب
    return render_template('OrderConfirmation.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
