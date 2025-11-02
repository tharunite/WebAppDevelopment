from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from models import User
from utils import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'patient')  # Default to patient
        
        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('auth/login.html')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Determine expected roles based on user_type
        if user_type == 'patient':
            expected_roles = ['patient']
        else:  # staff
            expected_roles = ['admin', 'doctor']
        
        cursor.execute('''
            SELECT id, username, password, role, fullname 
            FROM users 
            WHERE username = ? AND is_blacklisted = 0
        ''', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            # Check if user role matches selected type
            if user_data['role'] not in expected_roles:
                if user_type == 'patient':
                    flash('Please select "Patient" login type for patient accounts.', 'error')
                else:
                    flash('Please select "Staff" login type for staff accounts.', 'error')
                return render_template('auth/login.html')
            
            # Verify password
            if check_password_hash(user_data['password'], password):
                user = User(user_data['id'], user_data['username'], user_data['role'], user_data['fullname'])
                login_user(user)
                flash(f'Welcome back, {user.fullname or user.username}!', 'success')
                
                # Redirect patients to homepage to see appointments, others to dashboard
                if user_data['role'] == 'patient':
                    return redirect(url_for('public.index'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        # Validation
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        if not fullname or not email or not phone:
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists. Please choose another.', 'error')
            conn.close()
            return render_template('auth/register.html')
        
        # Check if email exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            flash('Email already registered. Please use a different email.', 'error')
            conn.close()
            return render_template('auth/register.html')
        
        # Create user (only patients can register)
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, password, role, fullname, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, 'patient', fullname, email, phone))
        user_id = cursor.lastrowid
        
        # Create patient record
        cursor.execute('''
            INSERT INTO patients (user_id)
            VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('public.index'))

