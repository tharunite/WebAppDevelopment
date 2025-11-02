from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
import sqlite3
from utils import role_required, get_db_connection

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/dashboard')
@login_required
@role_required('patient')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get patient ID
    cursor.execute('SELECT id FROM patients WHERE user_id = ?', (current_user.id,))
    patient = cursor.fetchone()
    if not patient:
        flash('Patient profile not found.', 'error')
        conn.close()
        return redirect(url_for('auth.logout'))
    
    patient_id = patient['id']
    
    # Get departments
    cursor.execute('SELECT id, name, description FROM departments ORDER BY name')
    departments = cursor.fetchall()
    
    # Get upcoming appointments
    cursor.execute('''
        SELECT a.id, a.appointment_date, a.appointment_time, a.status,
               u.fullname as doctor_name, dept.name as department
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE a.patient_id = ? AND a.status = "Booked"
        ORDER BY a.appointment_date, a.appointment_time
    ''', (patient_id,))
    upcoming_appointments = cursor.fetchall()
    
    conn.close()
    
    return render_template('patient/dashboard.html', 
                         departments=departments, 
                         upcoming_appointments=upcoming_appointments)

@patient_bp.route('/department/<int:department_id>')
@login_required
@role_required('patient')
def view_department(department_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, description FROM departments WHERE id = ?', (department_id,))
    department = cursor.fetchone()
    
    if not department:
        flash('Department not found.', 'error')
        conn.close()
        return redirect(url_for('patient.dashboard'))
    
    # Get doctors in this department
    cursor.execute('''
        SELECT d.id, u.fullname, d.specialization, d.experience_years, 
               d.qualification, d.bio
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE d.department_id = ? AND u.is_blacklisted = 0
        ORDER BY u.fullname
    ''', (department_id,))
    doctors = cursor.fetchall()
    
    conn.close()
    
    return render_template('patient/department.html', department=department, doctors=doctors)

@patient_bp.route('/doctor/<int:doctor_id>')
@login_required
@role_required('patient')
def view_doctor(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.id, u.fullname, d.specialization, d.experience_years, 
               d.qualification, d.bio, dept.name as department
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE d.id = ? AND u.is_blacklisted = 0
    ''', (doctor_id,))
    doctor = cursor.fetchone()
    
    if not doctor:
        flash('Doctor not found.', 'error')
        conn.close()
        return redirect(url_for('patient.dashboard'))
    
    conn.close()
    
    return render_template('patient/doctor_profile.html', doctor=doctor)

@patient_bp.route('/doctor/<int:doctor_id>/availability', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def check_availability(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.id, u.fullname, d.specialization
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE d.id = ? AND u.is_blacklisted = 0
    ''', (doctor_id,))
    doctor = cursor.fetchone()
    
    if not doctor:
        flash('Doctor not found.', 'error')
        conn.close()
        return redirect(url_for('patient.dashboard'))
    
    # Get patient ID
    cursor.execute('SELECT id FROM patients WHERE user_id = ?', (current_user.id,))
    patient = cursor.fetchone()
    patient_id = patient['id']
    
    # Get availability for next 7 days
    today = date.today()
    dates = [(today + timedelta(days=i)) for i in range(7)]
    
    cursor.execute('''
        SELECT date, morning_start, morning_end, evening_start, evening_end
        FROM doctor_availability
        WHERE doctor_id = ? AND date >= ? AND date <= ?
        ORDER BY date
    ''', (doctor_id, today, today + timedelta(days=7)))
    availability = {str(row['date']): row for row in cursor.fetchall()}
    
    # Get existing appointments for this doctor
    cursor.execute('''
        SELECT appointment_date, appointment_time
        FROM appointments
        WHERE doctor_id = ? AND status = "Booked"
    ''', (doctor_id,))
    booked_slots = [[str(row['appointment_date']), row['appointment_time']] for row in cursor.fetchall()]
    
    if request.method == 'POST':
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        
        if not appointment_date or not appointment_time:
            flash('Please select a date and time.', 'error')
            conn.close()
            return render_template('patient/availability.html', 
                                 doctor=doctor, dates=dates, 
                                 availability=availability, booked_slots=booked_slots)
        
        # Check if slot is already booked
        is_booked = any(slot[0] == appointment_date and slot[1] == appointment_time for slot in booked_slots)
        if is_booked:
            flash('This time slot is already booked. Please choose another.', 'error')
            conn.close()
            return render_template('patient/availability.html', 
                                 doctor=doctor, dates=dates, 
                                 availability=availability, booked_slots=booked_slots)
        
        # Check if slot is in doctor's availability
        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        if appointment_date in availability:
            avail = availability[appointment_date]
            time_obj = datetime.strptime(appointment_time, '%H:%M').time()
            
            is_available = False
            if avail['morning_start'] and avail['morning_end']:
                morning_start = datetime.strptime(avail['morning_start'], '%H:%M').time()
                morning_end = datetime.strptime(avail['morning_end'], '%H:%M').time()
                if morning_start <= time_obj <= morning_end:
                    is_available = True
            
            if not is_available and avail['evening_start'] and avail['evening_end']:
                evening_start = datetime.strptime(avail['evening_start'], '%H:%M').time()
                evening_end = datetime.strptime(avail['evening_end'], '%H:%M').time()
                if evening_start <= time_obj <= evening_end:
                    is_available = True
            
            if not is_available:
                flash('Selected time is not in doctor\'s availability.', 'error')
                conn.close()
                return render_template('patient/availability.html', 
                                     doctor=doctor, dates=dates, 
                                     availability=availability, booked_slots=booked_slots)
        else:
            flash('Doctor is not available on this date.', 'error')
            conn.close()
            return render_template('patient/availability.html', 
                                 doctor=doctor, dates=dates, 
                                 availability=availability, booked_slots=booked_slots)
        
        # Create appointment
        cursor.execute('''
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status)
            VALUES (?, ?, ?, ?, "Booked")
        ''', (patient_id, doctor_id, appointment_date, appointment_time))
        
        conn.commit()
        conn.close()
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.dashboard'))
    
    conn.close()
    
    return render_template('patient/availability.html', 
                         doctor=doctor, dates=dates, 
                         availability=availability, booked_slots=booked_slots)

@patient_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@role_required('patient')
def cancel_appointment(appointment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get patient ID
    cursor.execute('SELECT id FROM patients WHERE user_id = ?', (current_user.id,))
    patient = cursor.fetchone()
    patient_id = patient['id']
    
    # Verify appointment belongs to this patient
    cursor.execute('SELECT id FROM appointments WHERE id = ? AND patient_id = ?', 
                   (appointment_id, patient_id))
    
    if cursor.fetchone():
        cursor.execute('UPDATE appointments SET status = "Cancelled" WHERE id = ?', (appointment_id,))
        conn.commit()
        flash('Appointment cancelled successfully!', 'success')
    else:
        flash('Appointment not found or access denied.', 'error')
    
    conn.close()
    return redirect(url_for('patient.dashboard'))

@patient_bp.route('/history')
@login_required
@role_required('patient')
def history():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get patient ID
    cursor.execute('SELECT id FROM patients WHERE user_id = ?', (current_user.id,))
    patient = cursor.fetchone()
    patient_id = patient['id']
    
    # Get all treatments
    cursor.execute('''
        SELECT t.id, t.visit_type, t.tests_done, t.diagnosis, t.prescription, 
               t.medicines, t.created_at, a.appointment_date,
               u.fullname as doctor_name, dept.name as department
        FROM treatments t
        JOIN appointments a ON t.appointment_id = a.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC, t.created_at DESC
    ''', (patient_id,))
    treatments = cursor.fetchall()
    
    conn.close()
    
    return render_template('patient/history.html', treatments=treatments)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def profile():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM patients WHERE user_id = ?', (current_user.id,))
    patient = cursor.fetchone()
    patient_id = patient['id']
    
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        age = request.form.get('age')
        gender = request.form.get('gender')
        address = request.form.get('address')
        blood_group = request.form.get('blood_group')
        
        # Update user
        cursor.execute('''
            UPDATE users SET fullname = ?, email = ?, phone = ?
            WHERE id = ?
        ''', (fullname, email, phone, current_user.id))
        
        # Update patient
        cursor.execute('''
            UPDATE patients SET age = ?, gender = ?, address = ?, blood_group = ?
            WHERE id = ?
        ''', (age, gender, address, blood_group, patient_id))
        
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.profile'))
    
    # GET request
    cursor.execute('''
        SELECT u.fullname, u.email, u.phone, p.age, p.gender, p.address, p.blood_group
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
    ''', (patient_id,))
    profile_data = cursor.fetchone()
    
    conn.close()
    
    return render_template('patient/profile.html', profile=profile_data)

@patient_bp.route('/search', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def search():
    query = request.args.get('query') or request.form.get('query', '')
    
    if not query:
        return render_template('patient/search.html', results=None)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    search_term = f'%{query}%'
    
    # Search doctors
    cursor.execute('''
        SELECT d.id, u.fullname, d.specialization, dept.name as department
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE (u.fullname LIKE ? OR d.specialization LIKE ? OR dept.name LIKE ?) 
        AND u.is_blacklisted = 0
    ''', (search_term, search_term, search_term))
    doctors = cursor.fetchall()
    
    conn.close()
    
    return render_template('patient/search.html', query=query, doctors=doctors)

