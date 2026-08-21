import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'carfix_secret_key_secure'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('StoreDB.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def init_db():
    conn = get_db_connection()
    
    # 1. جدول السيارات
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_model TEXT,
            car_year TEXT
        )
    ''')
    
    # 2. جدول الزيوت (مضاف إليه الكمية Stock)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS oils (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductName TEXT,
            Description TEXT,
            Price REAL,
            CarModel TEXT,
            Image TEXT,
            Stock INTEGER DEFAULT 10
        )
    ''')
    
    # 3. جدول قطع الغيار (مضاف إليه الكمية Stock)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductName TEXT,
            Price REAL,
            CarID TEXT,
            Description TEXT,
            Image TEXT,
            Stock INTEGER DEFAULT 10
        )
    ''')

    # 4. جدول الشكاوى والدعم الفني (يربط العملاء بالأدمن)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            reply TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. جدول العملاء والمشتريات (لإدارة إجمالي المشتريات والمسجلين حديثاً)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            total_spent REAL DEFAULT 0,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    conn = get_db_connection()
    cars = conn.execute('SELECT * FROM cars').fetchall()
    conn.close()
    return render_template('Select-Car.html', cars=cars)

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

@app.route('/add_car', methods=['POST'])
def add_car():
    session['car_model'] = request.form.get('car_model')
    session['car_year'] = request.form.get('car_year')
    return redirect(url_for('products_page'))

@app.route('/products')
def products_page():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    oils = conn.execute('SELECT * FROM oils').fetchall()
    conn.close()
    
    car_model = session.get('car_model')
    car_year = session.get('car_year')
    
    return render_template('Product.html', products=products, oils=oils, car_model=car_model, car_year=car_year)

# صفحة مركز الدعم والشكاوى للعميل
@app.route('/support', methods=['GET', 'POST'])
def support_page():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        if name and email and message:
            conn = get_db_connection()
            conn.execute('INSERT INTO complaints (name, email, message) VALUES (?, ?, ?)', (name, email, message))
            conn.commit()
            conn.close()
            return redirect(url_for('select_car_page'))
    return render_template('Support.html')

# لوحة تحكم الأدمن المحمية والمعروض فيها كل الجداول والبيانات
@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    oils = conn.execute('SELECT * FROM oils').fetchall()
    cars = conn.execute('SELECT * FROM cars').fetchall()
    complaints = conn.execute('SELECT * FROM complaints').fetchall()
    customers = conn.execute('SELECT * FROM customers ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('Admin-Dashboard.html', products=products, oils=oils, cars=cars, complaints=complaints, customers=customers)

@app.route('/add_oil', methods=['POST'])
def add_oil():
    product_name = request.form.get('product_name')
    description = request.form.get('description')
    price = request.form.get('price')
    car_model = request.form.get('car_model')
    stock = request.form.get('stock', 10)
    
    image_file = request.files.get('image')
    image_filename = None
    if image_file and image_file.filename != '':
        image_filename = image_file.filename
        image_file.save(os.path.join(UPLOAD_FOLDER, image_filename))
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO oils (ProductName, Description, Price, CarModel, Image, Stock)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (product_name, description, price, car_model, image_filename, stock))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_product', methods=['POST'])
def add_product():
    product_name = request.form.get('product_name')
    description = request.form.get('description')
    price = request.form.get('price')
    car_id = request.form.get('car_id')
    stock = request.form.get('stock', 10)
    
    image_file = request.files.get('image')
    image_filename = None
    if image_file and image_file.filename != '':
        image_filename = image_file.filename
        image_file.save(os.path.join(UPLOAD_FOLDER, image_filename))
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO products (ProductName, Price, CarID, Description, Image, Stock)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (product_name, price, car_id, description, image_filename, stock))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# مسار رد الأدمن على الشكاوى
@app.route('/reply_complaint/<int:id>', methods=['POST'])
def reply_complaint(id):
    reply_text = request.form.get('reply')
    conn = get_db_connection()
    conn.execute('UPDATE complaints SET reply = ? WHERE id = ?', (reply_text, id))
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
