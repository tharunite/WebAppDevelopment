from flask import Flask, render_template, request,redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/submit', methods=['POST'])
def submit_feedback():
    name = request.form.get('name', 'Guest')
    feedback = request.form.get('feedback', 'No feedback provided')

    # redirect to thankyou with values in URL
    return redirect(url_for('thankyou', name=name, feedback=feedback))

@app.route('/thankyou')
def thankyou():
    name = request.args.get('name', 'Guest')
    feedback = request.args.get('feedback', 'No feedback provided')
    return render_template('thankyou.html', name=name, feedback=feedback)


if __name__ == "__main__":
    app.run(debug=True)
