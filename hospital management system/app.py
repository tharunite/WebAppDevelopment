from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hospital-management-system-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Database initialization
def init_db():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            fullname TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_blacklisted INTEGER DEFAULT 0
        )
    ''')
    
    # Departments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            specialization TEXT,
            department_id INTEGER,
            experience_years INTEGER,
            qualification TEXT,
            bio TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    ''')
    
    # Patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            age INTEGER,
            gender TEXT,
            address TEXT,
            blood_group TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT DEFAULT 'Booked',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')
    
    # Treatments table (patient history)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            visit_type TEXT,
            tests_done TEXT,
            diagnosis TEXT,
            prescription TEXT,
            medicines TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    ''')
    
    # Doctor availability table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            date DATE NOT NULL,
            morning_start TIME,
            morning_end TIME,
            evening_start TIME,
            evening_end TIME,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            UNIQUE(doctor_id, date)
        )
    ''')
    
    conn.commit()
    
    # Create default admin user
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, role, fullname, email)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin', admin_password, 'admin', 'Hospital Admin', 'admin@hospital.com'))
    
    # Create default departments (Comprehensive hospital departments)
    departments = [
        ('Cardiology', 'Heart and cardiovascular system care including cardiac surgery and interventional cardiology'),
        ('Cardiothoracic Surgery', 'Advanced surgical procedures for heart, lungs, and chest conditions'),
        ('Oncology', 'Comprehensive cancer treatment including chemotherapy, radiation, and surgical oncology'),
        ('Medical Oncology', 'Medical treatment of cancer with targeted therapies and immunotherapy'),
        ('Surgical Oncology', 'Surgical removal of tumors and cancer-related procedures'),
        ('Radiation Oncology', 'Radiation therapy for cancer treatment'),
        ('General Medicine', 'Primary care and internal medicine for adults'),
        ('Neurology', 'Diagnosis and treatment of brain and nervous system disorders'),
        ('Neurosurgery', 'Surgical treatment of brain, spine, and nervous system conditions'),
        ('Pediatrics', 'Specialized healthcare for infants, children, and adolescents'),
        ('Pediatric Surgery', 'Surgical procedures for children including congenital defects'),
        ('Orthopedics', 'Bone, joint, and muscle surgery including joint replacements'),
        ('Orthopedic Surgery', 'Advanced orthopedic procedures and trauma surgery'),
        ('Dermatology', 'Skin, hair, and nail condition diagnosis and treatment'),
        ('Ophthalmology', 'Eye care including cataract surgery, LASIK, and retinal procedures'),
        ('ENT (Ear, Nose, Throat)', 'Otolaryngology services for ear, nose, throat, head and neck conditions'),
        ('Urology', 'Urinary tract and male reproductive system care'),
        ('Nephrology', 'Kidney disease treatment including dialysis'),
        ('Gastroenterology', 'Digestive system disorders and treatment'),
        ('Gastrointestinal Surgery', 'Surgical procedures for digestive system conditions'),
        ('Hepatology', 'Liver disease treatment and transplantation'),
        ('Pulmonology', 'Lung and respiratory system care'),
        ('Endocrinology', 'Hormone and metabolic disorder treatment including diabetes'),
        ('Rheumatology', 'Autoimmune and joint inflammatory condition treatment'),
        ('Psychiatry', 'Mental health treatment and counseling'),
        ('Psychiatry and Behavioral Sciences', 'Comprehensive mental health care'),
        ('Anesthesiology', 'Anesthesia services for surgical procedures'),
        ('Radiology', 'Medical imaging including MRI, CT, ultrasound, and X-ray'),
        ('Pathology', 'Laboratory testing and disease diagnosis'),
        ('Emergency Medicine', '24/7 emergency care and trauma treatment'),
        ('Intensive Care (ICU)', 'Critical care for severely ill patients'),
        ('Gynecology', 'Women\'s reproductive health care'),
        ('Obstetrics', 'Pregnancy and childbirth care'),
        ('Obstetrics & Gynecology', 'Women\'s health including pregnancy and gynecological surgery'),
        ('Plastic Surgery', 'Cosmetic and reconstructive surgery'),
        ('Vascular Surgery', 'Blood vessel surgery and treatment'),
        ('General Surgery', 'Common surgical procedures including laparoscopic surgery'),
        ('Trauma Surgery', 'Emergency surgery for injuries and trauma'),
        ('Geriatrics', 'Healthcare for elderly patients'),
        ('Physiotherapy', 'Physical therapy and rehabilitation'),
        ('Dental', 'Oral and dental health care'),
        ('Orthodontics', 'Dental alignment and braces')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO departments (name, description)
        VALUES (?, ?)
    ''', departments)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

from models import User

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role, fullname FROM users WHERE id = ? AND is_blacklisted = 0', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[3])
    return None


# Import routes (after app and login_manager setup)
from routes import auth_routes, admin_routes, doctor_routes, patient_routes, public_routes

app.register_blueprint(public_routes.public_bp)
app.register_blueprint(auth_routes.auth_bp)
app.register_blueprint(admin_routes.admin_bp)
app.register_blueprint(doctor_routes.doctor_bp)
app.register_blueprint(patient_routes.patient_bp)

@app.route('/')
def index():
    # Always show landing page, even if logged in
    return redirect(url_for('public.index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'doctor':
        return redirect(url_for('doctor.dashboard'))
    elif current_user.role == 'patient':
        return redirect(url_for('patient.dashboard'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)

