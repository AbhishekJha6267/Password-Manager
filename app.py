import sqlite3
import bcrypt
import secrets
import string
import re
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import os

app = Flask(__name__)
CORS(app)

# Generate or load encryption key
KEY_FILE = 'secret.key'
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)

cipher = Fernet(key)

def init_db():
    conn = sqlite3.connect('passwords.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS passwords
                 (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, 
                  encrypted_password TEXT, url TEXT, username TEXT, 
                  created_at TEXT, expires_at TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    conn.commit()
    conn.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def encrypt_password(password):
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    return cipher.decrypt(encrypted_password.encode()).decode()

def generate_password(length=12, include_symbols=True):
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def check_password_strength(password):
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("At least 8 characters")
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Uppercase letter")
    
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Lowercase letter")
    
    if re.search(r'\d', password):
        score += 1
    else:
        feedback.append("Number")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append("Special character")
    
    strength = ["Very Weak", "Weak", "Fair", "Good", "Strong"][min(score, 4)]
    return {"strength": strength, "score": score, "missing": feedback}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    conn = sqlite3.connect('passwords.db')
    c = conn.cursor()
    
    try:
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                 (username, hashed_pw))
        conn.commit()
        return jsonify({"message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect('passwords.db')
    c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user and verify_password(password, user[1]):
        return jsonify({"user_id": user[0], "message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/passwords', methods=['GET'])
def list_passwords():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    conn = sqlite3.connect('passwords.db')
    c = conn.cursor()
    c.execute("""SELECT id, title, encrypted_password, url, username, 
                        created_at, expires_at FROM passwords WHERE user_id = ?""", 
              (user_id,))
    passwords = c.fetchall()
    conn.close()
    
    result = []
    for p in passwords:
        decrypted_pw = decrypt_password(p[2])
        expired = False
        if p[6]:  # expires_at
            expired = datetime.now() > datetime.fromisoformat(p[6])
        
        result.append({
            "id": p[0],
            "title": p[1],
            "password": decrypted_pw,
            "url": p[3],
            "username": p[4],
            "created_at": p[5],
            "expires_at": p[6],
            "expired": expired
        })
    
    return jsonify(result)

@app.route('/passwords', methods=['POST'])
def add_password():
    data = request.json
    user_id = data.get('user_id')
    title = data.get('title')
    password = data.get('password')
    url = data.get('url', '')
    username = data.get('username', '')
    expires_days = data.get('expires_days')
    
    if not all([user_id, title, password]):
        return jsonify({"error": "User ID, title, and password required"}), 400
    
    encrypted_pw = encrypt_password(password)
    created_at = datetime.now().isoformat()
    expires_at = None
    
    if expires_days:
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
    
    conn = sqlite3.connect('passwords.db')
    c = conn.cursor()
    c.execute("""INSERT INTO passwords (user_id, title, encrypted_password, url, 
                                       username, created_at, expires_at) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (user_id, title, encrypted_pw, url, username, created_at, expires_at))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Password added successfully"})

@app.route('/passwords/<int:password_id>', methods=['PUT'])
def update_password():
    data = request.json
    user_id = data.get('user_id')
    title = data.get('title')
    password = data.get('password')
    url = data.get('url', '')
    username = data.get('username', '')
    expires_days = data.get('expires_days')
    
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    conn = sqlite3.connect('passwords.db')
    c = conn.cursor()
    
    # Verify ownership
    c.execute("SELECT user_id FROM passwords WHERE id = ?", (password_id,))
    result = c.fetchone()
    if not result or result[0] != user_id:
        conn.close()
        return jsonify({"error": "Password not found or access denied"}), 404
    
    updates = []
    values = []
    
    if title:
        updates.append("title = ?")
        values.append(title)
    if password:
        updates.append("encrypted_password = ?")
        values.append(encrypt_password(password))
    if url is not None:
        updates.append("url = ?")
        values.append(url)
    if username is not None:
        updates.append("username = ?")
        values.append(username)
    if expires_days is not None:
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat() if expires_days > 0 else None
        updates.append("expires_at = ?")
        values.append(expires_at)
    
    if updates:
        values.append(password_id)
        c.execute(f"UPDATE passwords SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    
    conn.close()
    return jsonify({"message": "Password updated successfully"})

@app.route('/generate-password', methods=['POST'])
def api_generate_password():
    data = request.json or {}
    length = data.get('length', 12)
    include_symbols = data.get('include_symbols', True)
    
    password = generate_password(length, include_symbols)
    strength = check_password_strength(password)
    
    return jsonify({"password": password, "strength": strength})

@app.route('/check-strength', methods=['POST'])
def api_check_strength():
    data = request.json
    password = data.get('password')
    
    if not password:
        return jsonify({"error": "Password required"}), 400
    
    strength = check_password_strength(password)
    return jsonify(strength)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)