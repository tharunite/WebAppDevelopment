from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
# IMPORTANT: Use a complex, random secret key for production
app.secret_key = "replace_with_a_random_secret"

@app.route('/', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect to welcome page
    if 'name' in session:
        return redirect(url_for('welcome'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '').strip()

        if not name or not password:
            flash("Both fields are required.", 'error')
            return redirect(url_for('login'))

        # Simple hardcoded authentication check
        if name == "testuser" and password == "testpass":
            session['name'] = name
            session['temp_password'] = password  # Stored for display demo only

            flash(f"Login successful. Welcome, {name}!", 'success')
            return redirect(url_for('welcome'))
        else:
            flash("Invalid name or password. Use testuser/testpass.", 'error')
            return redirect(url_for('login'))

    # Render login form on GET request
    return render_template('login.html')

@app.route('/welcome')
def welcome():
    name = session.get('name')
    password = session.get('temp_password')

    # Access control check
    if not name:
        flash("Access denied. Please log in first.", 'warning')
        return redirect(url_for('login'))

    return render_template('welcome.html', name=name, password=password)

@app.route('/logout')
def logout():
    # Clear the session variables
    session.pop('name', None)
    session.pop('temp_password', None)
    flash("You have been logged out.", 'info')
    return redirect(url_for('login'))

if __name__ == "__main__":
    # Ensure this file is run from the terminal to start the server
    app.run(debug=True)