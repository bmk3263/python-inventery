import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_killercoda_key'

# Fetch Database Connection Details from Environment Variables
DB_HOST = os.environ.get('DB_HOST', 'postgres-service')
DB_NAME = os.environ.get('DB_NAME', 'sampledb')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASSWORD', 'postgres123')

def get_db_connection():
    # Retry logic while K8s starts the DB container
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
            )
            return conn
        except psycopg2.OperationalError:
            print("Waiting for database connection...")
            time.sleep(2)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            item TEXT,
            status TEXT,
            stock INTEGER
        )
    ''')
    
    # Seed Data
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users VALUES ('admin', 'password123')")
        
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO inventory (item, status, stock) VALUES (%s, %s, %s)", [
            ("Laptop", "Available", 15),
            ("Smartphone", "Out of Stock", 0),
            ("Wireless Headphones", "Available", 42)
        ])
        
    conn.commit()
    cursor.close()
    conn.close()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Flask to PostgreSQL</title></head>
<body style="font-family: Arial; margin: 40px;">
    {% if page == 'login' %}
        <h2>Login (PostgreSQL Connected)</h2>
        {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit">Login</button>
        </form>
    {% else %}
        <h2>Welcome, {{ username }}! <a href="/logout">Logout</a></h2>
        <h3>Live Inventory Data from PostgreSQL Instance</h3>
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr><th>ID</th><th>Item</th><th>Status</th><th>Stock</th></tr>
            {% for row in data %}
            <tr><td>{{ row.id }}</td><td>{{ row.item }}</td><td>{{ row.status }}</td><td>{{ row.stock }}</td></tr>
            {% endfor %}
        </table>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def home():
    if 'username' in session:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM inventory')
        inventory_items = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template_string(HTML_TEMPLATE, page='dashboard', username=session['username'], data=inventory_items)
    return render_template_string(HTML_TEMPLATE, page='login')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        session['username'] = username
        return redirect(url_for('home'))
    return render_template_string(HTML_TEMPLATE, page='login', error="Invalid Credentials")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
