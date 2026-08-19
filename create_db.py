import sqlite3

def create_database():
    # الاتصال بقاعدة البيانات الوحيدة StoreDB.db
    conn = sqlite3.connect('StoreDB.db')
    cursor = conn.cursor()

    # تفعيل العلاقات بين الجداول
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. جدول المستخدمين (العملاء والأدمن)
    cursor.execute('''
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

    # 2. جدول السيارات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cars (
            CarID INTEGER PRIMARY KEY AUTOINCREMENT,
            ModelName TEXT NOT NULL,
            Year INTEGER NOT NULL
        )
    ''')

    # 3. جدول المنتجات (قطع الغيار)
    cursor.execute('''
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

    # 4. جدول الشكاوي
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Complaints (
            ComplaintID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER,
            Message TEXT NOT NULL,
            Reply TEXT,
            FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
        )
    ''')

    # 5. جدول المشتريات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Purchases (
            PurchaseID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER,
            TotalAmount REAL NOT NULL,
            FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print("تم ضبط وإنشاء قاعدة البيانات والجداول بنجاح يا غالي!")

if __name__ == '__main__':
    create_database()