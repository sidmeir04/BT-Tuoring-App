from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import csv
from sqlalchemy import desc, asc
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from flask_mail import Message
from flask_login import LoginManager, UserMixin
from flask_login import login_user, current_user, logout_user, login_required


import functions

user_type_key = {0:'student',
                 1:'teacher',
                 2:'administrator',
                 3:'developer'}

app = Flask(__name__)
login_manager = LoginManager(app)
login_manager.login_view = 'login' #specify the login route

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255),unique=True)
    name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return self.username

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user):return
    # return User.get(user)

@app.route("/")
def index():
    #if logged in, go to dashboard
    #else go to login
    return render_template('index.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials!","danger")
    return render_template("login.html")

@app.route('/register', methods = ['POST','GET'])
def register():
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        username = request.form.get("username")
        print(name, last_name, email, password, confirm_password, username)
        # Validate form data (add your own validation logic)
        if not (
            name
            and last_name
            and email
            and password
            and confirm_password
            and username
        ):
            print('test')
        # Handle invalid input
            flash("Please fill in all fields.", "danger")
            return render_template("register.html")
        #handle if existing user
        user = User.query.filter_by(email=email).first()
        if user is not None and email == user.email:
            # Handle password mismatch
            flash("User already exist! Try a different email", "danger")
            return render_template("register.html")
        if password != confirm_password:
            # Handle password mismatch
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        # Create a new user instance
        new_user = User(
            name=name,
            last_name=last_name,
            email=email,
            username=username,
        )
        new_user.set_password(password)

        # Save the new user to the database
        print('adding user to database')
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created successfully! Please check your email to verify.", "success")
        return redirect(url_for('login'))
    return render_template("register.html")


@app.route('/charts')
def charts():
    return render_template('charts.html')

@app.route('/forgot')
def forgot():
    return render_template('forgot-password.html') 

# @app.route('/login')
# def login():
#     return render_template('login.html')

# @app.route('/login')
# def login():
#     return render_template('login.html')

# @app.route('/login')
# def login():
#     return render_template('login.html')

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.secret_key = "super_secret_key"  # Change this to a random, secure key
    app.run(debug=True)