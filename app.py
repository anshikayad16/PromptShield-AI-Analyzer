from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db
from model import pipeline
import os

from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Secret key for sessions
app.secret_key = os.urandom(24)

# Ensure DB is initialized
with app.app_context():
    init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone() is not None:
            flash("Username already exists", "error")
            conn.close()
            return render_template('register.html')
            
        hashed_pw = generate_password_hash(password)
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()
        
        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    c = conn.cursor()
    # Fetch user logs
    c.execute("SELECT prompt, result, layer, timestamp FROM logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20", (session['user_id'],))
    logs = [dict(row) for row in c.fetchall()]
    
    # Get stats for graphs
    c.execute("SELECT COUNT(*) as count FROM logs WHERE user_id = ? AND result = 'Safe'", (session['user_id'],))
    safe_count = c.fetchone()['count']
    c.execute("SELECT COUNT(*) as count FROM logs WHERE user_id = ? AND result = 'Blocked'", (session['user_id'],))
    blocked_count = c.fetchone()['count']
    
    conn.close()
    
    return render_template('dashboard.html', logs=logs, safe_count=safe_count, blocked_count=blocked_count)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    # If using typical web Dashboard, they have a session.
    # Otherwise from extension to bypass auth, default to 1.
    user_id = session.get('user_id', 1)
        
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400
        
    # Process through pipeline
    decision = pipeline.analyze_prompt(prompt)
    
    # Store to DB
    conn = get_db_connection()
    c = conn.cursor()
    
    # Ensure extension_user exists (id 1 usually if first)
    c.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'extension_user', 'no_pass')")
    
    c.execute(
        "INSERT INTO logs (user_id, prompt, result, layer) VALUES (?, ?, ?, ?)",
        (user_id, prompt, decision['status'], decision['layer'])
    )
    conn.commit()
    conn.close()
    
    # Simulate AI Response if safe
    response_text = ""
    if decision['status'] == 'Safe':
        response_text = f"AI Response: I have received your safe prompt and processed it."
    else:
        response_text = f"Blocked due to security reasons."
        
    return jsonify({
        "status": decision["status"],
        "layer": decision["layer"],
        "reason": decision["reason"],
        "response": response_text
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
