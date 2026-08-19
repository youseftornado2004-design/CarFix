from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'carfix_secret_key_secure_completely'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('StoreDB.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON;")
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Phone TEXT,
            Email TEXT UNIQUE NOT NULL,
            Password TEXT NOT NULL,
            Gender TEXT,
            BirthDate TEXT,
            IsAdmin INTEGER DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Cars (
            CarID INTEGER PRIMARY KEY AUTOINCREMENT,
            ModelName TEXT NOT NULL,
            Year INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Products (
            ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductName TEXT NOT NULL,
            Price REAL NOT NULL,
            CarID INTEGER,
            Description TEXT,
            Image TEXT,
            Stock INTEGER DEFAULT 10,
            FOREIGN KEY (CarID) REFERENCES Cars(CarID) ON DELETE CASCADE
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Complaints (
            ComplaintID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER,
            Message TEXT NOT NULL,
            Reply TEXT,
            FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Purchases (
            PurchaseID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER,
            TotalAmount REAL NOT NULL,
            FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
        )
    ''')
    
    try:
        conn.execute('ALTER TABLE Products ADD COLUMN Stock INTEGER DEFAULT 10')
        conn.commit()
    except sqlite3.OperationalError:
        pass 
    conn.close()

init_db()

# السطرين دول هم اللي بيخلي الموقع يفتح صفحة التسجيل لوحده أول ما تفتح الرابط السادة
@app.route('/')
def home():
    return redirect(url_for('register_page'))

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    error = None
    if request.method == 'POST':
        first_name = request.form.get('FirstName')
        last_name = request.form.get('LastName')
        birth_date = request.form.get('BirthDate')
        gender = request.form.get('Gender')
        phone = request.form.get('Phone')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO Users (FirstName, LastName, Phone, Email, Password, Gender, BirthDate, IsAdmin) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            ''', (first_name, last_name, phone, email, password, gender, birth_date))
            conn.commit()
            conn.close()
            return redirect(url_for('login_page'))
        except sqlite3.IntegrityError:
            error = 'البريد الإلكتروني أو رقم الهاتف مسجل مسبقاً!'
        conn.close()
    return render_template('Register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE Email = ? AND Password = ?', (email, password)).fetchone()
        conn.close()
        
        if user:
            session['user_email'] = user['Email']
            session['user_id'] = user['UserID']
            session['is_admin'] = user['IsAdmin']
            if user['IsAdmin'] == 1:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('select_car_page'))
        else:
            error = 'البريد الإلكتروني أو كلمة المرور غير صحيحة!'
    return render_template('login.html', error=error)

@app.route('/admin')
def admin_dashboard():
    if 'user_email' not in session or not session.get('is_admin'):
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    try:
        complaints = conn.execute('''
            SELECT Complaints.ComplaintID, Complaints.Message, Users.FirstName, Users.LastName, Users.Email 
            FROM Complaints 
            JOIN Users ON Complaints.UserID = Users.UserID
            WHERE Complaints.Reply IS NULL OR Complaints.Reply = ''
        ''').fetchall()
        
        purchases = conn.execute('''
            SELECT Users.FirstName, Users.LastName, Users.Email, Users.Phone, Purchases.TotalAmount
            FROM Purchases
            JOIN Users ON Purchases.UserID = Users.UserID
        ''').fetchall()
        
        cars = conn.execute('SELECT * FROM Cars').fetchall()
        registered_users = conn.execute('SELECT FirstName, LastName, Email, Phone, BirthDate, Gender FROM Users WHERE IsAdmin = 0').fetchall()
    except sqlite3.OperationalError as e:
        print("DB Error:", e)
        complaints, purchases, cars, registered_users = [], [], [], []
    conn.close()
    return render_template('Admin-Dashboard.html', complaints=complaints, purchases=purchases, cars=cars, registered_users=registered_users)

@app.route('/admin/reply-complaint', methods=['POST'])
def reply_complaint():
    if 'user_email' not in session or not session.get('is_admin'):
        return redirect(url_for('login_page'))
    complaint_id = request.form.get('complaint_id')
    reply_text = request.form.get('reply_text')
    conn = get_db_connection()
    try:
        conn.execute('UPDATE Complaints SET Reply = ? WHERE ComplaintID = ?', (reply_text, complaint_id))
        conn.commit()
    except:
        pass
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-car', methods=['POST'])
def admin_add_car():
    if 'user_email' not in session or not session.get('is_admin'):
        return redirect(url_for('login_page'))
    brand = request.form.get('Brand')
    year = request.form.get('Year')
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO Cars (ModelName, Year) VALUES (?, ?)', (brand, year))
        conn.commit()
    except Exception as e:
        print("Car Add Error:", e)
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-product', methods=['POST'])
def admin_add_product():
    if 'user_email' not in session or not session.get('is_admin'):
        return redirect(url_for('login_page'))
    name = request.form.get('ProductName')
    price = request.form.get('Price')
    car_id = request.form.get('CarID')
    description = request.form.get('Description', 'قطعة غيار أصلية')
    stock = request.form.get('Stock', 10)
    
    image_filename = ''
    if 'ProductImage' in request.files:
        file = request.files['ProductImage']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO Products (ProductName, Price, CarID, Description, Image, Stock) VALUES (?, ?, ?, ?, ?, ?)', 
                     (name, price, car_id, description, image_filename, stock))
        conn.commit()
    except Exception as e:
        print("Product Add Error:", e)
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/select-car')
def select_car_page():
    if 'user_email' not in session:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    cars = conn.execute('SELECT * FROM Cars').fetchall()
    conn.close()
    return render_template('Select-Car.html', cars=cars)

@app.route('/product')
def product_page():
    if 'user_email' not in session:
        return redirect(url_for('login_page'))
    
    car_id = request.args.get('CarID')
    car_model = request.args.get('CarModel')
    car_year = request.args.get('CarYear')
    
    conn = get_db_connection()
    products = []
    try:
        if car_id:
            car_info = conn.execute('SELECT * FROM Cars WHERE CarID = ?', (car_id)).fetchone()
            if car_info:
                car_model = car_info['ModelName']
                car_year = car_info['Year']
            products = conn.execute('''
                SELECT Products.*, Cars.ModelName, Cars.Year FROM Products 
                JOIN Cars ON Products.CarID = Cars.CarID 
                WHERE Products.CarID = ? AND Products.Stock > 0
            ''', (car_id,)).fetchall()
        elif car_model and car_year:
            products = conn.execute('''
                SELECT Products.*, Cars.ModelName, Cars.Year FROM Products 
                JOIN Cars ON Products.CarID = Cars.CarID 
                WHERE Cars.ModelName = ? AND Cars.Year = ? AND Products.Stock > 0
            ''', (car_model, car_year)).fetchall()
        else:
            products = conn.execute('''
                SELECT Products.*, Cars.ModelName, Cars.Year FROM Products 
                LEFT JOIN Cars ON Products.CarID = Cars.CarID
                WHERE Products.Stock > 0
            ''').fetchall()
    except Exception as e:
        print("Product Page Error:", e)
        products = []
    conn.close()
    return render_template('Product.html', products=products, car_model=car_model, car_year=car_year)

@app.route('/submit-complaint', methods=['POST'])
def submit_complaint():
    if 'user_email' not in session:
        return redirect(url_for('login_page'))
    message = request.form.get('message')
    user_id = session.get('user_id')
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO Complaints (UserID, Message) VALUES (?, ?)', (user_id, message))
        conn.commit()
    except:
        pass
    conn.close()
    return redirect(url_for('select_car_page'))

@app.route('/save-purchase', methods=['POST'])
def save_purchase():
    if 'user_email' not in session:
        return {'status': 'unauthorized'}, 401
        
    data = request.json
    total_amount = data.get('total', 0)
    items = data.get('items', [])
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO Purchases (UserID, TotalAmount) VALUES (?, ?)', (user_id, total_amount))
        
        for item in items:
            prod_id = item.get('id')
            qty = item.get('quantity', 1)
            conn.execute('UPDATE Products SET Stock = Stock - ? WHERE ProductID = ?', (qty, prod_id))
            
        conn.commit()
    except Exception as e:
        print("Purchase Error:", e)
    conn.close()
    return {'status': 'success'}

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
