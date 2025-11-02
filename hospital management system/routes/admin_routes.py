from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import sqlite3
from utils import role_required, get_db_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get counts
    cursor.execute('SELECT COUNT(*) FROM doctors')
    doctor_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM patients')
    patient_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE status = "Booked"')
    appointment_count = cursor.fetchone()[0]
    
    # Get doctors
    cursor.execute('''
        SELECT d.id, u.fullname, d.specialization, dept.name as department, d.experience_years, u.is_blacklisted
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        ORDER BY u.fullname
    ''')
    doctors = cursor.fetchall()
    
    # Get patients
    cursor.execute('''
        SELECT p.id, u.fullname, u.email, u.phone, u.is_blacklisted
        FROM patients p
        JOIN users u ON p.user_id = u.id
        ORDER BY u.fullname
    ''')
    patients = cursor.fetchall()
    
    # Get upcoming appointments
    cursor.execute('''
        SELECT a.id, u1.fullname as patient_name, u2.fullname as doctor_name, 
               dept.name as department, a.appointment_date, a.appointment_time, a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u1 ON p.user_id = u1.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u2 ON d.user_id = u2.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE a.status = "Booked"
        ORDER BY a.appointment_date, a.appointment_time
    ''')
    upcoming_appointments = cursor.fetchall()
    
    # Get past appointments (Completed and Cancelled)
    cursor.execute('''
        SELECT a.id, u1.fullname as patient_name, u2.fullname as doctor_name, 
               dept.name as department, a.appointment_date, a.appointment_time, a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u1 ON p.user_id = u1.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u2 ON d.user_id = u2.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE a.status IN ("Completed", "Cancelled")
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        LIMIT 50
    ''')
    past_appointments = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         doctor_count=doctor_count, 
                         patient_count=patient_count,
                         appointment_count=appointment_count,
                         doctors=doctors,
                         patients=patients,
                         upcoming_appointments=upcoming_appointments,
                         past_appointments=past_appointments)

@admin_bp.route('/doctor/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_doctor():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        specialization = request.form.get('specialization')
        department_id = request.form.get('department_id')
        experience_years = request.form.get('experience_years')
        qualification = request.form.get('qualification')
        bio = request.form.get('bio')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if not username or not password or not fullname or not specialization:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('admin.create_doctor'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists.', 'error')
            conn.close()
            return redirect(url_for('admin.create_doctor'))
        
        # Create user
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, password, role, fullname, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, 'doctor', fullname, email, phone))
        user_id = cursor.lastrowid
        
        # Create doctor record
        cursor.execute('''
            INSERT INTO doctors (user_id, specialization, department_id, experience_years, qualification, bio)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, specialization, department_id, experience_years, qualification, bio))
        
        conn.commit()
        conn.close()
        
        flash('Doctor created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM departments ORDER BY name')
    departments = cursor.fetchall()
    conn.close()
    
    return render_template('admin/create_doctor.html', departments=departments)

@admin_bp.route('/doctor/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_doctor(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        specialization = request.form.get('specialization')
        department_id = request.form.get('department_id')
        experience_years = request.form.get('experience_years')
        qualification = request.form.get('qualification')
        bio = request.form.get('bio')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        cursor.execute('SELECT user_id FROM doctors WHERE id = ?', (doctor_id,))
        doctor = cursor.fetchone()
        if not doctor:
            flash('Doctor not found.', 'error')
            conn.close()
            return redirect(url_for('admin.dashboard'))
        
        user_id = doctor['user_id']
        
        # Update user
        cursor.execute('''
            UPDATE users SET fullname = ?, email = ?, phone = ?
            WHERE id = ?
        ''', (fullname, email, phone, user_id))
        
        # Update doctor
        cursor.execute('''
            UPDATE doctors SET specialization = ?, department_id = ?, 
            experience_years = ?, qualification = ?, bio = ?
            WHERE id = ?
        ''', (specialization, department_id, experience_years, qualification, bio, doctor_id))
        
        conn.commit()
        conn.close()
        
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    # GET request
    cursor.execute('''
        SELECT d.id, d.specialization, d.department_id, d.experience_years, 
               d.qualification, d.bio, u.fullname, u.email, u.phone
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE d.id = ?
    ''', (doctor_id,))
    doctor = cursor.fetchone()
    
    cursor.execute('SELECT id, name FROM departments ORDER BY name')
    departments = cursor.fetchall()
    
    conn.close()
    
    if not doctor:
        flash('Doctor not found.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/edit_doctor.html', doctor=doctor, departments=departments)

@admin_bp.route('/doctor/<int:doctor_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_doctor(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id FROM doctors WHERE id = ?', (doctor_id,))
    doctor = cursor.fetchone()
    
    if doctor:
        cursor.execute('DELETE FROM doctors WHERE id = ?', (doctor_id,))
        cursor.execute('DELETE FROM users WHERE id = ?', (doctor['user_id'],))
        conn.commit()
        flash('Doctor deleted successfully!', 'success')
    else:
        flash('Doctor not found.', 'error')
    
    conn.close()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/doctor/<int:doctor_id>/blacklist', methods=['POST'])
@login_required
@role_required('admin')
def blacklist_doctor(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id FROM doctors WHERE id = ?', (doctor_id,))
    doctor = cursor.fetchone()
    
    if doctor:
        cursor.execute('UPDATE users SET is_blacklisted = 1 WHERE id = ?', (doctor['user_id'],))
        conn.commit()
        flash('Doctor blacklisted successfully!', 'success')
    else:
        flash('Doctor not found.', 'error')
    
    conn.close()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/patient/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        age = request.form.get('age')
        gender = request.form.get('gender')
        address = request.form.get('address')
        blood_group = request.form.get('blood_group')
        
        cursor.execute('SELECT user_id FROM patients WHERE id = ?', (patient_id,))
        patient = cursor.fetchone()
        if not patient:
            flash('Patient not found.', 'error')
            conn.close()
            return redirect(url_for('admin.dashboard'))
        
        user_id = patient['user_id']
        
        # Update user
        cursor.execute('''
            UPDATE users SET fullname = ?, email = ?, phone = ?
            WHERE id = ?
        ''', (fullname, email, phone, user_id))
        
        # Update patient
        cursor.execute('''
            UPDATE patients SET age = ?, gender = ?, address = ?, blood_group = ?
            WHERE id = ?
        ''', (age, gender, address, blood_group, patient_id))
        
        conn.commit()
        conn.close()
        
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    # GET request
    cursor.execute('''
        SELECT p.id, u.fullname, u.email, u.phone, p.age, p.gender, p.address, p.blood_group
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
    ''', (patient_id,))
    patient = cursor.fetchone()
    
    conn.close()
    
    if not patient:
        flash('Patient not found.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/edit_patient.html', patient=patient)

@admin_bp.route('/patient/<int:patient_id>/blacklist', methods=['POST'])
@login_required
@role_required('admin')
def blacklist_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id FROM patients WHERE id = ?', (patient_id,))
    patient = cursor.fetchone()
    
    if patient:
        cursor.execute('UPDATE users SET is_blacklisted = 1 WHERE id = ?', (patient['user_id'],))
        conn.commit()
        flash('Patient blacklisted successfully!', 'success')
    else:
        flash('Patient not found.', 'error')
    
    conn.close()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/search', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def search():
    query = request.args.get('query') or request.form.get('query', '')
    
    if not query:
        return render_template('admin/search.html', results=None)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    search_term = f'%{query}%'
    
    # Search doctors
    cursor.execute('''
        SELECT d.id, u.fullname, d.specialization, dept.name as department
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE u.fullname LIKE ? OR d.specialization LIKE ? OR dept.name LIKE ?
    ''', (search_term, search_term, search_term))
    doctors = cursor.fetchall()
    
    # Search patients
    cursor.execute('''
        SELECT p.id, u.fullname, u.email, u.phone
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.fullname LIKE ? OR u.email LIKE ? OR u.phone LIKE ?
    ''', (search_term, search_term, search_term))
    patients = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/search.html', query=query, doctors=doctors, patients=patients)

@admin_bp.route('/appointment/<int:appointment_id>/history')
@login_required
@role_required('admin')
def view_patient_history(appointment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.id, u1.fullname as patient_name, u2.fullname as doctor_name, 
               dept.name as department, a.appointment_date, a.appointment_time
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u1 ON p.user_id = u1.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u2 ON d.user_id = u2.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE a.id = ?
    ''', (appointment_id,))
    appointment = cursor.fetchone()
    
    if not appointment:
        flash('Appointment not found.', 'error')
        conn.close()
        return redirect(url_for('admin.dashboard'))
    
    # Get all treatments for this patient
    cursor.execute('''
        SELECT t.id, t.visit_type, t.tests_done, t.diagnosis, t.prescription, 
               t.medicines, t.created_at, a.appointment_date
        FROM treatments t
        JOIN appointments a ON t.appointment_id = a.id
        WHERE a.patient_id = (SELECT patient_id FROM appointments WHERE id = ?)
        ORDER BY a.appointment_date DESC, t.created_at DESC
    ''', (appointment_id,))
    treatments = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/patient_history.html', appointment=appointment, treatments=treatments)

