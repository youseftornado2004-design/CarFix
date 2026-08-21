import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('StoreDB.db')
    conn.row_factory = sqlite3.Row
    return conn

# دالة إعادة إنشاء وتحديث الجداول بأمان تام بدون أخطاء
def init_db():
    conn = get_db_connection()
    # لو الجدول القديم فيه مشكلة في الأعمدة، بنحذفه وننشئه بالهيكل السليم
    conn.execute('DROP TABLE IF EXISTS cars')
    conn.execute('''
        CREATE TABLE cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_model TEXT,
            car_year TEXT
        )
    ''')
    
    # جدول الزيوت
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

# صفحة اختيار السيارة
@app.route('/select-car')
def select_car_page():
    conn = get_db_connection()
    try:
        cars = conn.execute('SELECT * FROM cars').fetchall()
    except:
        cars = []
    conn.close()
    return render_template('Select-Car.html', cars=cars)

# مسار إضافة سيارة جديدة من لوحة تحكم الأدمن
@app.route('/admin_add_car', methods=['POST'])
def admin_add_car():
    car_model = request.form.get('car_model')
    car_year = request.form.get('car_year')
    
    if car_model and car_year:
        conn = get_db_connection()
        conn.execute('INSERT INTO cars (car_model, car_year) VALUES (?, ?)', (car_model, car_year))
        conn.commit()
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

# مسار اختيار العميل لعربيته
@app.route('/add_car', methods=['POST'])
def add_car():
    session['car_model'] = request.form.get('car_model')
    session['car_year'] = request.form.get('car_year')
    return redirect(url_for('products_page'))

# صفحة المنتجات والزيوت
@app.route('/products')
def products_page():
    conn = get_db_connection()
    try:
        products = conn.execute('SELECT * FROM products').fetchall()
    except:
        products = []
        
    oils = conn.execute('SELECT * FROM oils').fetchall()
    conn.close()
    
    car_model = session.get('car_model')
    car_year = session.get('car_year')
    
    return render_template('Product.html', products=products, oils=oils, car_model=car_model, car_year=car_year)

# لوحة تحكم الأدمن
@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    try:
        products = conn.execute('SELECT * FROM products').fetchall()
    except:
        products = []
        
    oils = conn.execute('SELECT * FROM oils').fetchall()
    cars = conn.execute('SELECT * FROM cars').fetchall()
    conn.close()
    return render_template('Admin-Dashboard.html', products=products, oils=oils, cars=cars)

# إضافة زيت جديد
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
    conn.execute('''
        INSERT INTO oils (ProductName, Description, Price, CarModel, Image)
        VALUES (?, ?, ?, ?, ?)
    ''', (product_name, description, price, car_model, image_filename))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/save-purchase', methods=['POST'])
def save_purchase():
    return jsonify({'status': 'success'})

@app.route('/order-confirmation')
def order_confirmation():
    return render_template('OrderConfirmation.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
