# Hospital Management System (HMS)

A comprehensive web application for managing hospital operations, including patient registration, doctor management, appointment scheduling, and treatment history tracking.

## Features

### Admin Features
- Dashboard with statistics (doctors, patients, appointments count)
- Create, edit, and delete doctor profiles
- Manage patient profiles
- View all appointments
- Search for doctors and patients
- Blacklist users
- View patient treatment history

### Doctor Features
- View upcoming appointments
- View assigned patients
- Update patient treatment history (diagnosis, prescription, medicines)
- Mark appointments as completed or cancelled
- Set availability for next 7 days (morning and evening slots)

### Patient Features
- Register and login
- Browse departments
- View doctor profiles and availability
- Book appointments
- Cancel appointments
- View treatment history
- Edit profile

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, Bootstrap 5, Jinja2 templating
- **Database**: SQLite
- **Authentication**: Flask-Login

## Installation

1. Install Python 3.8 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Access the application at `http://localhost:5000`

## Default Login Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`

## Database

The database is created programmatically when the application starts. The database file `hospital.db` will be created automatically.

### Tables
- `users` - User accounts (admin, doctor, patient)
- `departments` - Medical departments
- `doctors` - Doctor profiles
- `patients` - Patient profiles
- `appointments` - Appointment records
- `treatments` - Patient treatment history
- `doctor_availability` - Doctor availability schedule

## Project Structure

```
hospital-management-system/
├── app.py                 # Main application file
├── routes/                # Route handlers
│   ├── __init__.py
│   ├── auth_routes.py     # Authentication routes
│   ├── admin_routes.py    # Admin routes
│   ├── doctor_routes.py   # Doctor routes
│   └── patient_routes.py  # Patient routes
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── auth/             # Authentication templates
│   ├── admin/            # Admin templates
│   ├── doctor/           # Doctor templates
│   └── patient/          # Patient templates
├── static/               # Static files
│   ├── css/
│   └── js/
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Core Features Implementation

### Appointment Management
- Prevents multiple appointments at the same time for the same doctor
- Status management: Booked → Completed → Cancelled
- Complete appointment history tracking

### Patient History
- Stores all completed appointment records
- Includes diagnosis, prescriptions, and doctor notes
- Accessible by patients, doctors, and admins

### Search Functionality
- Admin: Search by doctor name, specialization, patient name, email, phone
- Patient: Search doctors by name or specialization

### Validation
- Frontend validation using HTML5 form validation
- Backend validation in route handlers
- Prevents unauthorized access using Flask-Login

## Security Features

- Password hashing using Werkzeug
- Session-based authentication
- Role-based access control
- Blacklist functionality for users
- SQL injection prevention using parameterized queries

## Usage Guidelines

1. **As Admin**: Login with admin credentials to manage the system
2. **As Doctor**: Admin must create doctor accounts first. Doctors can then login and set their availability
3. **As Patient**: Patients can register themselves and book appointments with available doctors

## Notes

- All database operations are created programmatically
- The admin user is created automatically on first run
- Default departments (Cardiology, Oncology, General, Neurology, Pediatrics) are created automatically
- Doctor availability must be set for patients to book appointments

## Development

This project uses Flask's development server. For production deployment, use a proper WSGI server like Gunicorn.

## License

This project is developed for educational purposes.

