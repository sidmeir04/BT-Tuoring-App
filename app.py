from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
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
from calendar import weekday
import json
from sqlalchemy.orm.attributes import flag_modified
from datetime import time
from flask import request, Flask
from flask_socketio import emit
from flask import Blueprint, render_template
from flask_socketio import SocketIO 

socketio = SocketIO()

main = Blueprint("main", __name__)

def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = True

    app.register_blueprint(main)

    socketio.init_app(app)

    return app

app = create_app()

users = {}

#the "connect" here is a keyword, when the server first starts it will say connected
@socketio.on("connect")
def handle_connect():
    print("Client connected!")

@socketio.on("user_join")
def handle_user_join(username):
    print(f"User {username} joined!")
    users[username] = request.sid

@socketio.on("new_message")
def handle_new_message(message):
    print(f"New message: {message}")
    username = None 
    for user in users:
        if users[user] == request.sid:
            username = user
    print(message,username)
    emit("chat", {"message": message, "username": username}, broadcast=True)

@app.route('/testing')
def testing_socketio():
    return render_template("index_temp.html")

import functions

user_type_key = {0:'student',
                 1:'teacher',
                 2:'administrator',
                 3:'developer'}

# app = Flask(__name__)
login_manager = LoginManager(app)
login_manager.login_view = 'login' #specify the login route

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
db = SQLAlchemy(app)

def load_default_schedule():
    with open('static/assets/default_schedule.json', 'r') as file:
        default_schedule = json.load(file)
    return default_schedule

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255),unique=True)
    name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Integer,nullable=False)
    schedule_data = db.Column(JSON, default=load_default_schedule)
    sessions = db.relationship('Session', backref='user', lazy = True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    subject = db.Column(db.String(255))
    tutor = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False) # Tutor's ID number
    email = db.Column(db.String(255), unique=True, nullable=False)
    completed = db.Column(db.Boolean, default = False)


class Periods(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    monday = db.Column(db.String(256), default = '')
    tuesday = db.Column(db.String(256), default = '')
    wednesday = db.Column(db.String(256), default = '')
    thursday = db.Column(db.String(256), default = '')
    friday = db.Column(db.String(256), default = '')

with app.app_context():
    db.create_all()

# to prevent needing to change all the html file templates
@app.route('/index.html')
def reroute_user():
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user):
    return User.get(user)

@app.route('/createDB')
def createDB():
    for _ in range(1,10):
        newThing = Periods()
        db.session.add(newThing)
        db.session.commit()
    new_user = User(name='name', last_name='last_name', email='oscjep25@bergen.org', username='username', role=int(1))
    new_user.set_password('pass')
    db.session.add(new_user)
    new_user = User(name='Student', last_name='Student2', email='student@gmail.com', username='Student', role=int(1))
    new_user.set_password('pass')
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/")
def index():
    #if logged in, go to dashboard
    #else go to login
    if not current_user.is_authenticated:return redirect(url_for('login'))

    if current_user.role == 0:
        number = .23
        if number > .75:
            color = 'success'
        elif number > .25:
            color = 'warning'
        else:
            color = 'danger'
        print(color)
        return render_template('index0.html',username=current_user.username,number=number,color=color)
    elif current_user.role == 1:
        return render_template('index1.html',username=current_user.username)
    return redirect(url_for('login'))

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

@app.route('/logout',methods=['POST'])
def logout():
    logout_user()
    flash('Logged out!','success')
    return redirect(url_for('login'))

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
        role = request.form.get('role')
        # Validate form data (add your own validation logic)
        if not (
            name
            and last_name
            and email
            and password
            and confirm_password
            and username
            and role
        ):
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
            role=int(role)
        )
        new_user.set_password(password)

        # Save the new user to the database
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created successfully! Please check your email to verify.", "success")
        return redirect(url_for('login'))
    return render_template("register.html")

def time_to_min(time):
    factors = (60, 1, 1/60)

    return sum(i*j for i, j in zip(map(int, time.split(':')), factors))

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
def date_to_day(date):
    year, month, day = (int(i) for i in date.split('-'))
    dayNumber = weekday(year, month, day)
    day = days[dayNumber].lower()
    return day

@app.route('/session_manager', methods = ['POST','GET'])
def session_manager():
    #use a 2d list that maps from a dictionary for each day and period, and then access
    users = []
    day = None
    date = None
    if request.method == 'POST':
        type = request.form.get('type')
        period = request.form.get('period')
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        day = date_to_day(date)
        period_data = Periods.query.get(period)
        if type == '1':
            user = current_user
            data = getattr(period_data, day, 'default')
            #Check that the times are correct
            # period_start = 450 + int(period)*45
            # period_end = period_start + 41
            # if period_start < time_to_min(start_time) < period_end or period_start < time_to_min(end_time) < period_end or time_to_min(end_time) > time_to_min(start_time):
            #     flash('invalid times', 'warning')
            #     return redirect(url_for('session_manager'))

            setattr(period_data, day, data + ' ' + str(user.id))
            user.schedule_data[day]['start_time'] = str(start_time)
            user.schedule_data[day]['end_time'] = str(end_time)
            flag_modified(user, 'schedule_data')
            db.session.commit()
        elif type == '0':
            data = getattr(period_data, day, '')
            user_ids = data.split(' ')
            for id in user_ids:
                user = User.query.get(id)
                users.append(user)
        
    return render_template('session_manager.html', users = users[1:], day = day, date = date)

def string_to_time(time_str):
    hour, minute = map(int, time_str.split(':'))
    # Create a time object with the provided hour and minute
    result_time = time(hour=hour, minute=minute)
    return result_time
    
@app.route('/book_session/<id>/<date>')
def book_session(id, date):
    user = User.query.get(id)
    day = date_to_day(date)
    data = user.schedule_data[day]
    new_session = Session(
        tutor = id,
        start_time = string_to_time(data['start_time']),
        end_time = string_to_time(data['end_time']),
        # subject = data['subject'],
        email = user.email,
    )
    db.session.add(new_session)
    db.session.commit()
    flash('Book Session', 'success')
    return redirect(url_for('session_manager'))

@app.route('/charts')
def charts():
    return render_template('charts.html')

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/buttons')
def buttons():
    return render_template('buttons.html') 

@app.route('/cards')
def cards():
    return render_template('cards.html')

@app.route('/tables')
def tables():
    return render_template('tables.html') 

@app.route('/utilities-animation')
def utilities_animation():
    return render_template('utilities-animation.html') 

@app.route('/utilities-border')
def utilities_border():
    return render_template('utilities-border.html') 

@app.route('/utilities-color')
def utilities_color():
    return render_template('utilities-color.html') 

@app.route('/utilities-other')
def utilities_other():
    return render_template('utilities-other.html') 

@app.route('/appointment_details')
def details():
    id = request.args.get()
    return render_template('appointment_details.html')

# @app.route('/login')
# def login():
#     return render_template('login.html')

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.secret_key = "ben_sucks"  # Change this to a random, secure key
    socketio.run(app)