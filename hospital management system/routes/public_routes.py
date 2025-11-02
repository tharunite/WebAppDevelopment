from flask import Blueprint, render_template
from flask_login import current_user
from utils import get_db_connection

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    pending_appointments = None
    
    # If patient is logged in, fetch their pending appointments
    if current_user.is_authenticated and current_user.role == 'patient':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get patient ID
        cursor.execute('SELECT id FROM patients WHERE user_id = ?', (current_user.id,))
        patient = cursor.fetchone()
        
        if patient:
            patient_id = patient['id']
            
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
            pending_appointments = cursor.fetchall()
        
        conn.close()
    
    return render_template('public/index.html', pending_appointments=pending_appointments)

@public_bp.route('/departments')
def departments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description FROM departments ORDER BY name')
    departments = cursor.fetchall()
    conn.close()
    return render_template('public/departments.html', departments=departments)

@public_bp.route('/treatments')
def treatments():
    treatments = [
        {
            'name': 'Robotic Heart Transplant', 
            'description': 'One of only 3 hospitals in India performing robotic-assisted heart transplants. Our advanced robotic surgery system enables minimally invasive procedures with precision and faster recovery.', 
            'icon': 'heart-pulse-fill',
            'premium': True
        },
        {
            'name': 'Deep Brain Stimulation (DBS)', 
            'description': 'Advanced neurosurgical procedure for Parkinson\'s and movement disorders. Only 3 hospitals in India offer this cutting-edge treatment. Our team has performed over 200 successful DBS procedures.', 
            'icon': 'brain',
            'premium': True
        },
        {
            'name': 'Robotic Kidney Transplant', 
            'description': 'Minimally invasive kidney transplant using da Vinci robotic system. One of only 3 hospitals in India with this capability. Reduces recovery time and complications significantly.', 
            'icon': 'droplet-fill',
            'premium': True
        },
        {
            'name': 'Complex Spine Reconstruction', 
            'description': 'Advanced spinal deformity correction and reconstruction. Our surgeons are among the few in India performing complex multi-level spinal fusions and reconstructions.', 
            'icon': 'back',
            'premium': True
        },
        {
            'name': 'Transcatheter Aortic Valve Replacement (TAVR)', 
            'description': 'Minimally invasive heart valve replacement. One of only 3 hospitals in India offering this procedure for high-risk patients who cannot undergo open-heart surgery.', 
            'icon': 'heart-fill',
            'premium': True
        },
        {
            'name': 'Liver Transplantation', 
            'description': 'Advanced liver transplant program with one of the highest success rates in the country. We perform both living and deceased donor liver transplants.', 
            'icon': 'lungs-fill',
            'premium': True
        },
        {
            'name': 'Heart Surgery', 
            'description': 'Advanced cardiac procedures including bypass surgery, valve replacement, and minimally invasive heart surgery using state-of-the-art technology.', 
            'icon': 'heart-fill'
        },
        {
            'name': 'Joint Replacement', 
            'description': 'Advanced orthopedic procedures including hip, knee, and shoulder replacement surgery with latest robotic-assisted technology.', 
            'icon': 'bone'
        },
        {
            'name': 'LASIK Eye Surgery', 
            'description': 'Advanced LASIK and refractive surgery procedures performed by experienced ophthalmologists with 99% success rate.', 
            'icon': 'eye-fill'
        },
        {
            'name': 'Pulmonary Care', 
            'description': 'Comprehensive respiratory care including treatment for asthma, COPD, and other lung conditions with advanced pulmonary rehabilitation.', 
            'icon': 'lungs-fill'
        },
        {
            'name': 'Cancer Immunotherapy', 
            'description': 'Cutting-edge cancer treatment using immunotherapy and targeted therapy for various cancer types with promising results.', 
            'icon': 'capsule'
        },
        {
            'name': 'Minimally Invasive Surgery', 
            'description': 'Laparoscopic and robotic-assisted surgeries for various conditions, reducing pain and recovery time significantly.', 
            'icon': 'scissors'
        }
    ]
    return render_template('public/treatments.html', treatments=treatments)

@public_bp.route('/success')
def success_stories():
    stories = [
        {
            'name': 'Rajesh Kumar',
            'role': 'Robotic Heart Transplant Patient',
            'quote': '"I was told by several hospitals that my condition was too complex. CityCare Hospital performed a robotic heart transplant that only 3 hospitals in India can do. The precision and care were outstanding. I\'m alive today because of their expertise."',
            'date': '2024',
            'procedure': 'Robotic Heart Transplant'
        },
        {
            'name': 'John Smith',
            'role': 'Cardiac Surgery Patient',
            'quote': '"The care I received at CityCare Hospital was exceptional. The doctors and staff were compassionate and professional throughout my heart surgery recovery. The facilities are world-class."',
            'date': '2024',
            'procedure': 'Cardiac Bypass Surgery'
        },
        {
            'name': 'Sarah Johnson',
            'role': 'Parent of Pediatric Patient',
            'quote': '"My 5-year-old daughter needed complex pediatric surgery. The pediatric team at CityCare was amazing. They made us feel comfortable and explained everything. My daughter recovered beautifully and is now back to playing!"',
            'date': '2024',
            'procedure': 'Pediatric Surgery'
        },
        {
            'name': 'Priya Sharma',
            'role': 'Deep Brain Stimulation Patient',
            'quote': '"After years of suffering from Parkinson\'s, I underwent Deep Brain Stimulation at CityCare - one of only 3 hospitals in India that performs this. The results were life-changing. My tremors are gone and I can live normally again."',
            'date': '2024',
            'procedure': 'Deep Brain Stimulation'
        },
        {
            'name': 'Michael Chen',
            'role': 'Orthopedic Surgery Patient',
            'quote': '"The orthopedic team helped me recover fully from my knee replacement. The rehabilitation program was excellent and I\'m back to my active lifestyle. The robotic-assisted surgery made recovery much faster."',
            'date': '2024',
            'procedure': 'Robotic Knee Replacement'
        },
        {
            'name': 'Anjali Patel',
            'role': 'Liver Transplant Patient',
            'quote': '"My liver transplant at CityCare was a success. The transplant team is among the best in the country. The post-operative care was exceptional. I\'m grateful to be healthy again and back to my family."',
            'date': '2023',
            'procedure': 'Liver Transplantation'
        },
        {
            'name': 'David Williams',
            'role': 'Complex Spine Surgery Patient',
            'quote': '"I had severe spinal deformity that multiple surgeons refused to operate on. CityCare Hospital\'s spine team took on my case and performed complex spine reconstruction. Today, I\'m pain-free and can walk straight. This hospital is truly exceptional."',
            'date': '2024',
            'procedure': 'Complex Spine Reconstruction'
        },
        {
            'name': 'Meera Reddy',
            'role': 'TAVR Procedure Patient',
            'quote': '"At 78, I was too high-risk for open-heart surgery. CityCare offered TAVR procedure which only 3 hospitals in India perform. It was minimally invasive, and I recovered in just 3 days! The technology here is incredible."',
            'date': '2024',
            'procedure': 'TAVR (Transcatheter Aortic Valve Replacement)'
        },
        {
            'name': 'Amit Singh',
            'role': 'Robotic Kidney Transplant Patient',
            'quote': '"My robotic kidney transplant at CityCare was amazing. One of only 3 hospitals in India with this capability. The recovery was much faster than traditional surgery. The surgical team\'s expertise is world-class."',
            'date': '2023',
            'procedure': 'Robotic Kidney Transplant'
        }
    ]
    return render_template('public/success_stories.html', stories=stories)

@public_bp.route('/about')
def about():
    return render_template('public/about.html')

@public_bp.route('/contact')
def contact():
    return render_template('public/contact.html')

@public_bp.route('/blog')
def blog():
    blogs = [
        {
            'id': 1,
            'title': 'Understanding Heart Health: A Complete Guide',
            'excerpt': 'Learn about maintaining a healthy heart, common cardiovascular conditions, and preventive measures you can take today.',
            'author': 'Dr. Rajesh Kumar',
            'date': '2024-01-15',
            'category': 'Cardiology',
            'image': 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800&h=400&fit=crop'
        },
        {
            'id': 2,
            'title': 'Robotic Surgery: The Future of Minimally Invasive Procedures',
            'excerpt': 'Discover how robotic-assisted surgery is revolutionizing healthcare, reducing recovery times, and improving patient outcomes.',
            'author': 'Dr. Priya Sharma',
            'date': '2024-01-10',
            'category': 'Technology',
            'image': 'https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=800&h=400&fit=crop'
        },
        {
            'id': 3,
            'title': 'Mental Health Matters: Breaking the Stigma',
            'excerpt': 'An important discussion about mental health awareness, available treatments, and how to support loved ones struggling with mental health issues.',
            'author': 'Dr. Sarah Johnson',
            'date': '2024-01-05',
            'category': 'Mental Health',
            'image': 'https://images.unsplash.com/photo-1576091160550-2173baa4f81d?w=800&h=400&fit=crop'
        },
        {
            'id': 4,
            'title': 'Pediatric Care: What Every Parent Should Know',
            'excerpt': 'Essential information about children\'s health, common childhood illnesses, vaccinations, and when to seek medical attention.',
            'author': 'Dr. Anjali Patel',
            'date': '2023-12-28',
            'category': 'Pediatrics',
            'image': 'https://images.unsplash.com/photo-1576091160550-2173baa4f81d?w=800&h=400&fit=crop'
        },
        {
            'id': 5,
            'title': 'Deep Brain Stimulation: Hope for Parkinson\'s Patients',
            'excerpt': 'An in-depth look at DBS therapy, one of the most advanced treatments for Parkinson\'s disease, available at only 3 hospitals in India.',
            'author': 'Dr. David Williams',
            'date': '2023-12-20',
            'category': 'Neurology',
            'image': 'https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=800&h=400&fit=crop'
        },
        {
            'id': 6,
            'title': 'Preventive Care: Your First Line of Defense',
            'excerpt': 'Learn why regular health checkups, screenings, and preventive measures are crucial for maintaining long-term health and wellness.',
            'author': 'Dr. Michael Chen',
            'date': '2023-12-15',
            'category': 'Preventive Care',
            'image': 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=800&h=400&fit=crop'
        }
    ]
    return render_template('public/blog.html', blogs=blogs)

