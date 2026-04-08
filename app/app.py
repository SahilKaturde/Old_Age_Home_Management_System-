import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Register Blueprints
from routes.resident import resident_bp
from routes.visitor import visitor_bp
from routes.admin import admin_bp

app.register_blueprint(resident_bp)
app.register_blueprint(visitor_bp)
app.register_blueprint(admin_bp)

# Basic route for testing
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        conn = Config.get_db_connection()
        cur = conn.cursor()
        
        # Determine table based on role
        table = 'admin' if role == 'admin' else ('resident' if role == 'resident' else 'visitor')
        
        try:
            cur.execute(f"SELECT * FROM {table} WHERE email = %s AND password = %s", (email, password))
            user = cur.fetchone()
            
            if user:
                session['user_id'] = user[0]
                session['role'] = role
                session['name'] = user[1]
                flash(f'Welcome back, {user[1]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials. Please try again.', 'error')
        except Exception as e:
            flash(f'Database error: {str(e)}', 'error')
        finally:
            cur.close()
            conn.close()

    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    conn = Config.get_db_connection()
    cur = conn.cursor()
    
    table = 'resident' if role == 'resident' else 'visitor'
    
    try:
        cur.execute(f"INSERT INTO {table} (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        flash('Registration successful! Please login.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Registration failed: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role')
    
    if role == 'resident':
        return redirect(url_for('resident.dashboard'))
    elif role == 'visitor':
        return redirect(url_for('visitor.dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin.dashboard'))
    else:
        # Fallback
        return f"<h1>Welcome, {session['name']}!</h1><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
