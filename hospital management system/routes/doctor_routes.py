from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
import sqlite3
from utils import role_required, get_db_connection

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor_bp.route('/dashboard')
@login_required
@role_required('doctor')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get doctor ID
    cursor.execute('SELECT id FROM doctors WHERE user_id = ?', (current_user.id,))
    doctor = cursor.fetchone()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        conn.close()
        return redirect(url_for('auth.logout'))
    
    doctor_id = doctor['id']
    
    # Get upcoming appointments for today and this week
    today = date.today()
    week_end = today + timedelta(days=7)
    cursor.execute('''
        SELECT a.id, a.appointment_date, a.appointment_time, a.status,
               u.fullname as patient_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.doctor_id = ? AND a.status = "Booked" 
        AND a.appointment_date >= ? AND a.appointment_date <= ?
        ORDER BY a.appointment_date, a.appointment_time
    ''', (doctor_id, today, week_end))
    appointments = cursor.fetchall()
    
    # Also get today's appointments specifically
    cursor.execute('''
        SELECT a.id, a.appointment_date, a.appointment_time, a.status,
               u.fullname as patient_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.doctor_id = ? AND a.status = "Booked" 
        AND a.appointment_date = ?
        ORDER BY a.appointment_time
    ''', (doctor_id, today))
    today_appointments = cursor.fetchall()
    
    # Get assigned patients (patients who have appointments)
    cursor.execute('''
        SELECT DISTINCT p.id, u.fullname, u.email
        FROM patients p
        JOIN users u ON p.user_id = u.id
        JOIN appointments a ON a.patient_id = p.id
        WHERE a.doctor_id = ?
        ORDER BY u.fullname
    ''', (doctor_id,))
    patients = cursor.fetchall()
    
    conn.close()
    
    return render_template('doctor/dashboard.html', 
                         appointments=appointments, 
                         today_appointments=today_appointments,
                         patients=patients)

@doctor_bp.route('/appointment/<int:appointment_id>/update', methods=['GET', 'POST'])
@login_required
@role_required('doctor')
def update_patient_history(appointment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify appointment belongs to this doctor
    cursor.execute('''
        SELECT a.id, a.patient_id, d.id as doctor_id, u.fullname as patient_name, 
               dept.name as department
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE a.id = ? AND d.user_id = ?
    ''', (appointment_id, current_user.id))
    appointment = cursor.fetchone()
    
    if not appointment:
        flash('Appointment not found or access denied.', 'error')
        conn.close()
        return redirect(url_for('doctor.dashboard'))
    
    if request.method == 'POST':
        visit_type = request.form.get('visit_type')
        tests_done = request.form.get('tests_done')
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        medicines = request.form.get('medicines')
        notes = request.form.get('notes')
        
        # Check if treatment already exists
        cursor.execute('SELECT id FROM treatments WHERE appointment_id = ?', (appointment_id,))
        treatment = cursor.fetchone()
        
        if treatment:
            # Update existing treatment
            cursor.execute('''
                UPDATE treatments SET visit_type = ?, tests_done = ?, diagnosis = ?,
                prescription = ?, medicines = ?, notes = ?
                WHERE appointment_id = ?
            ''', (visit_type, tests_done, diagnosis, prescription, medicines, notes, appointment_id))
        else:
            # Create new treatment
            cursor.execute('''
                INSERT INTO treatments (appointment_id, visit_type, tests_done, diagnosis, prescription, medicines, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (appointment_id, visit_type, tests_done, diagnosis, prescription, medicines, notes))
        
        conn.commit()
        conn.close()
        
        flash('Patient history updated successfully!', 'success')
        return redirect(url_for('doctor.dashboard'))
    
    # GET request - check if treatment exists
    cursor.execute('''
        SELECT visit_type, tests_done, diagnosis, prescription, medicines, notes
        FROM treatments
        WHERE appointment_id = ?
    ''', (appointment_id,))
    treatment = cursor.fetchone()
    
    conn.close()
    
    return render_template('doctor/update_history.html', appointment=appointment, treatment=treatment)

@doctor_bp.route('/appointment/<int:appointment_id>/complete', methods=['POST'])
@login_required
@role_required('doctor')
def complete_appointment(appointment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify appointment belongs to this doctor
    cursor.execute('''
        SELECT a.id FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.id = ? AND d.user_id = ?
    ''', (appointment_id, current_user.id))
    
    if cursor.fetchone():
        cursor.execute('UPDATE appointments SET status = "Completed" WHERE id = ?', (appointment_id,))
        conn.commit()
        flash('Appointment marked as completed!', 'success')
    else:
        flash('Appointment not found or access denied.', 'error')
    
    conn.close()
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@role_required('doctor')
def cancel_appointment(appointment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify appointment belongs to this doctor
    cursor.execute('''
        SELECT a.id FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.id = ? AND d.user_id = ?
    ''', (appointment_id, current_user.id))
    
    if cursor.fetchone():
        cursor.execute('UPDATE appointments SET status = "Cancelled" WHERE id = ?', (appointment_id,))
        conn.commit()
        flash('Appointment cancelled!', 'success')
    else:
        flash('Appointment not found or access denied.', 'error')
    
    conn.close()
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/patient/<int:patient_id>/history')
@login_required
@role_required('doctor')
def view_patient_history(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify patient is assigned to this doctor
    cursor.execute('SELECT id FROM doctors WHERE user_id = ?', (current_user.id,))
    doctor = cursor.fetchone()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        conn.close()
        return redirect(url_for('doctor.dashboard'))
    
    doctor_id = doctor['id']
    
    cursor.execute('''
        SELECT p.id, u.fullname
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
    ''', (patient_id,))
    patient = cursor.fetchone()
    
    if not patient:
        flash('Patient not found.', 'error')
        conn.close()
        return redirect(url_for('doctor.dashboard'))
    
    # Get all treatments for this patient with this doctor
    cursor.execute('''
        SELECT t.id, t.visit_type, t.tests_done, t.diagnosis, t.prescription, 
               t.medicines, t.created_at, a.appointment_date
        FROM treatments t
        JOIN appointments a ON t.appointment_id = a.id
        WHERE a.patient_id = ? AND a.doctor_id = ?
        ORDER BY a.appointment_date DESC, t.created_at DESC
    ''', (patient_id, doctor_id))
    treatments = cursor.fetchall()
    
    conn.close()
    
    return render_template('doctor/patient_history.html', patient=patient, treatments=treatments)

@doctor_bp.route('/availability', methods=['GET', 'POST'])
@login_required
@role_required('doctor')
def availability():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM doctors WHERE user_id = ?', (current_user.id,))
    doctor = cursor.fetchone()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        conn.close()
        return redirect(url_for('doctor.dashboard'))
    
    doctor_id = doctor['id']
    
    if request.method == 'POST':
        # Get availability for next 7 days
        today = date.today()
        
        # Delete existing availability for next 7 days
        end_date = today + timedelta(days=7)
        cursor.execute('''
            DELETE FROM doctor_availability 
            WHERE doctor_id = ? AND date >= ? AND date <= ?
        ''', (doctor_id, today, end_date))
        
        # Insert new availability
        for i in range(7):
            day = today + timedelta(days=i)
            morning_start = request.form.get(f'morning_start_{i}')
            morning_end = request.form.get(f'morning_end_{i}')
            evening_start = request.form.get(f'evening_start_{i}')
            evening_end = request.form.get(f'evening_end_{i}')
            
            if morning_start and morning_end:
                cursor.execute('''
                    INSERT INTO doctor_availability (doctor_id, date, morning_start, morning_end, evening_start, evening_end)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (doctor_id, day, morning_start, morning_end, evening_start, evening_end))
        
        conn.commit()
        conn.close()
        
        flash('Availability updated successfully!', 'success')
        return redirect(url_for('doctor.dashboard'))
    
    # GET request - show form with next 7 days
    today = date.today()
    dates = [(today + timedelta(days=i)) for i in range(7)]
    
    # Get existing availability
    cursor.execute('''
        SELECT date, morning_start, morning_end, evening_start, evening_end
        FROM doctor_availability
        WHERE doctor_id = ? AND date >= ? AND date <= ?
        ORDER BY date
    ''', (doctor_id, today, today + timedelta(days=7)))
    existing_availability = {str(row['date']): row for row in cursor.fetchall()}
    
    conn.close()
    
    return render_template('doctor/availability.html', dates=dates, existing_availability=existing_availability)

