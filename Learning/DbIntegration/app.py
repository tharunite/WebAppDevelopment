from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app=Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///users.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False

db=SQLAlchemy(app)

@app.route('/')
def home():
    return "database connected"
if __name__=="__main__":
    app.run(debug=True)
