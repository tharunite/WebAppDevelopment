from flask import Flask,render_template,request

app=Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/thankyou')
def feedback():
    name=request.args.get('name') or "Guest"
    feedback=request.args.get('feedback') or "No feedback provided"
    return render_template('thankyou.html',name=name,feedback=feedback)

if __name__=="__main__":
    app.run(debug=True)
