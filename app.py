from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
import random
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
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
from datetime import time, timedelta
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

@app.route('/appointment_details')
def details():
    ID = request.args.get('identification')
    open_sesssion = Session.query.get(ID)
    message_history = MessageHistory.query.get(open_sesssion.message_history_id)
    messages = message_history.messages['list']
    messages = [{'mine': True if i['sender'] == current_user.username else False,'message':i['message']}  for i in messages]
    print(messages)
    return render_template('appointment_details.html',session=open_sesssion,history=open_sesssion.message_history_id,thiss=current_user,messages=messages)


@socketio.on("connect")
def handle_connect():
    print(request.sid)
    print("Client connected!")

@socketio.on("user_join")
def handle_user_join(user_id,history_id):
    #bug check 1: this part works
    history = MessageHistory.query.get(history_id)
    history.people[user_id] = request.sid
    flag_modified(history,'people')
    db.session.commit()

@socketio.on("new_message")
def handle_new_message(message,username,history_id):
    history = MessageHistory.query.get(history_id)
    print(history)
    people = history.people
    choose = [i for i in people.keys()]
    print(choose)
    print(current_user.id)
    other = choose[0] if choose[0] != str(current_user.id) else choose[1]
    print(other)
    #saves all messages to the database
    history.messages['list'].append({'message':message,'sender':username})
    flag_modified(history,'messages')
    db.session.commit()
    emit("chat", {"message": message, "username": username}, room=history.people[other])


user_type_key = {0:'student',
                 1:'teacher',
                 2:'administrator',
                 3:'developer'}

# app = Flask(__name__)
login_manager = LoginManager(app)
login_manager.login_view = 'login' #specify the login route

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
app.config['SESSION_COOKIE_NAME'] = 'Session_Cookie'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # For HTTPS only
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # Recommended for security
app.config['SESSION_PERMANENT'] = False  # Session only lasts until the browser is closed

db = SQLAlchemy(app)

def load_basic_json_file():
    with open('static/assets/basic_json_file.json', 'r') as file:
        basic = json.load(file)
    return basic

def load_default_schedule():
    with open('static/assets/default_schedule.json', 'r') as file:
        default_schedule = json.load(file)
    return default_schedule

def load_default_notifactions():
    with open('static/assets/default_notifactions.json', 'r') as file:
        default_notifactions = json.load(file)
    return default_notifactions

def load_non_basic_json_file():
    with open('static/assets/messages.json', 'r') as file:
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
    notifaction_data = db.Column(JSON, default=load_default_notifactions)
    sessions = db.relationship('Session', backref='user', lazy = True)
    feedbacks = db.relationship('Feedback', backref='user', lazy = True)
    hours_of_service = db.Column(db.Float, default = 0.0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MessageHistory(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    people = db.Column(JSON, default=load_basic_json_file)
    messages = db.Column(JSON, default=load_non_basic_json_file)
    session = db.relationship('Session', backref='message_history', lazy = True)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    date = db.Column(db.Date)
    subject = db.Column(db.String(255))
    tutor = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False) # Tutor's ID number
    student = db.Column(db.Integer, nullable = False)
    period = db.Column(db.Integer)
    tutor_form_completed = db.Column(db.Boolean, default = False)
    student_form_completed = db.Column(db.Boolean, default = False)
    message_history_id = db.Column(db.Integer, db.ForeignKey('message_history.id'))

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    on_time = db.Column(db.Integer)
    understanding = db.Column(db.Integer)
    date = db.Column(db.String(255))
    review_text = db.Column(db.String(255))
    subject = db.Column(db.String(255))
    tutoring = db.Column(db.Boolean)
    review_for = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False) # Tutor's ID number
    review_from = db.Column(db.String(255), nullable = False)


class Periods(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    monday = db.Column(db.String(256), default = '')
    tuesday = db.Column(db.String(256), default = '')
    wednesday = db.Column(db.String(256), default = '')
    thursday = db.Column(db.String(256), default = '')
    friday = db.Column(db.String(256), default = '')



with app.app_context():
    db.create_all()

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/delete_notification', methods=['POST'])
@login_required
def delete_notification():
    data = request.get_json()
    notification = data.get('notif')
    if notification in current_user.notifaction_data['deleted']:
        current_user.notifaction_data['deleted'].remove(notification)
        flag_modified(current_user, "notifaction_data")
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False})

# to prevent needing to change all the html file templates
@app.route('/index.html')
def reroute_user():
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user):
    return User.get(int(user))

@app.route('/createDB')
def createDB():
    for _ in range(1,10):
        newThing = Periods()
        db.session.add(newThing)
        db.session.commit()
    new_user = User(name='name', last_name='last_name', email='oscjep25@bergen.org', username='username', role=int(0))
    new_user.set_password('pass')
    db.session.add(new_user)
    new_user = User(name='Student', last_name='Student2', email='student@gmail.com', username='Student', role=int(0))
    new_user.set_password('pass')
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/")
def index():
    #if logged in, go to dashboard
    #else go to login
    if not current_user.is_authenticated:return redirect(url_for('login'))
    # if current_user.role == 0:
    number = 4.20    
    if number > .75:
        color = 'success'
    elif number > .25:
        color = 'warning'
    else:
        color = 'danger'

    return render_template('index0.html',username=current_user.username,number=number,color=color, sessions = Session.query.filter_by(tutor=current_user.id, tutor_form_completed = False).all(), student_sessions = Session.query.filter_by(student=current_user.id, student_form_completed = False).all())


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
    return render_template("user_handling/login.html")

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
            return render_template("user_handling/register.html")

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
    return render_template("user_handling/register.html")

@app.route('/complete_session/<id>')
def complete_session(id):
    session = Session.query.get(id)
    ##############################################################################################################################

                                        # add for final product #

    ##############################################################################################################################
    # date = session.date
    # today = datetime.now().date()
    # if date >= today:
    #     flash('Tutoring Session has not Happened yet', 'warning')
    #     return redirect(url_for('index'))
    if current_user.id == session.tutor:
        return redirect(f"/completion_form?type={2}&id={session.id}")
    if current_user.id == session.student:
        return redirect(f"/completion_form?type={1}&id={session.id}")
    return redirect(url_for('index'))

@app.route('/completion_form/', methods = ['GET','POST'])
def completion_form():
    type = request.args.get('type')
    id = request.args.get('id')
    if request.method == 'POST':
        understanding = request.form.get('personal_rating')
        on_time = request.form.get('on_time')
        review = request.form.get('message')
        session = Session.query.get(id)
        if int(type) == 1:
            review_for = session.tutor
        else:
            review_for = session.student
        feedback = Feedback(
            on_time = on_time,
            understanding = understanding,
            date = datetime.today().strftime('%Y-%m-%d'),
            review_text = review,
            review_for = review_for,    
            review_from = current_user.username,
            subject = session.subject
        )
        if int(current_user.id) == int(session.tutor):
            session.tutor_form_completed = True
            feedback.tutoring = False
        else:
            session.student_form_completed = True
            feedback.tutoring = True

        db.session.add(feedback)
        db.session.commit()
        if session.tutor_form_completed and session.student_form_completed:
            tutor = User.query.get(session.tutor)
            datetime1 = datetime.combine(datetime.today(), session.end_time)
            datetime2 = datetime.combine(datetime.today(), session.start_time)
            difference =  datetime1 - datetime2
            difference = difference.total_seconds()/3600
            tutor.hours_of_service += float(difference)
            db.session.commit()
            return redirect(f'/delete_session/{session.id}/1')
        return redirect(url_for('index'))
    return render_template('completion_form.html', type = type, id = id)

@app.route('/show_feedback')
def show_feedback():
    reviews = Feedback.query.filter_by(review_for = current_user.id)
    return render_template('show_feedback.html', reviews = reviews)

def time_to_min(time):
    factors = (60, 1, 1/60)

    return sum(i*j for i, j in zip(map(int, time.split(':')), factors))

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
def date_to_day(date):
    year, month, day = (int(i) for i in date.split('-'))
    dayNumber = weekday(year, month, day)
    day = days[dayNumber].lower()
    return day

lower_days = ['monday','tuesday','wednesday','thursday','friday']
def find_next_day_of_week(day_of_week):
    day_index = lower_days.index(day_of_week.lower())
    today = datetime.now().weekday()
    days_ahead = (day_index - today) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_day = datetime.now() + timedelta(days=days_ahead)

    return next_day.strftime("%Y-%m-%d")

@app.route('/find_session',methods=['GET','POST'])
def find_session():
    users = []
    day = None
    date = None
    tutor_name = ''
    users = []

    if request.method == 'POST':
        date = request.form.get('modal_date')
        period = request.form.get('period')
        tutor_name = request.form.get('specific_tutor')
        # send to the front end, use jinja if to only show the session if that tutor is assigned
        subject = request.form.get('subject')
        if not tutor_name:
            tutor_name = ''
        users = []
        user_names = []
        if period != '-1':
            data = Periods.query.get(int(period))
            if date:
                day = date_to_day(date)
                data = getattr(data, day, 'defualt')
                user_names = [(User.query.get(int(id)).username,id,period,date) for id in data.split(' ')[1:]]
                users = [User.query.get(int(id)).schedule_data[day][period] for id in data.split(' ')[1:]]
            else:
                for day in lower_days:
                    day_data = getattr(data, day, 'defualt')
                    [user_names.append((User.query.get(int(id)).username,id,period,find_next_day_of_week(day))) for id in day_data.split(' ')[1:]]
                    [users.append(User.query.get(int(id)).schedule_data[day][period]) for id in day_data.split(' ')[1:]]
        elif date:
            day = date_to_day(date)
            day_data = [getattr(Periods.query.get(i),day) for i in range(1,10)]
            for period,period_data in enumerate(day_data):
                if period_data:
                    [user_names.append((User.query.get(int(id)).username,id,period+1,date)) for id in period_data.split(' ')[1:]]
                    [users.append(User.query.get(int(id)).schedule_data[day][str(period+1)]) for id in period_data.split(' ')[1:]]
        return render_template('find_session.html', users = users, user_names = user_names, enumerate = enumerate,tutor_name=tutor_name.lower())
    return render_template('find_session.html', enumerate = enumerate,tutor_name=tutor_name.lower())

@app.route('/scheduler',methods=['POST','GET'])
def scheduler():
    if request.method == 'POST':
        thing = request.form.get('modalPass').split(',')
        period,day = int(thing[0])+1,thing[1]
        day = int(day)
        period_data = Periods.query.get(period)
        data = getattr(period_data, lower_days[day], 'default')
        if ('delete', '') not in request.form.items():
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            period_start = 450 + int(period)*45
            period_end = period_start + 41
            start_min = time_to_min(start_time)
            end_min = time_to_min(end_time)
            if (start_min < period_start or end_min > period_end or start_min > end_min):
                flash('invalid times', 'warning')
                return redirect(url_for('scheduler'))
            current_user.schedule_data[lower_days[day]][str(period)]['start_time'] = start_time
            current_user.schedule_data[lower_days[day]][str(period)]['end_time'] = end_time
            current_user.schedule_data[lower_days[day]][str(period)]['times'] = ''
            current_user.schedule_data[lower_days[day]][str(period)]['subject'] = 'random'
            if str(current_user.id) not in getattr(period_data, lower_days[day], 'default').split(' '):
                setattr(period_data, lower_days[day], data + ' ' + str(current_user.id))

        else:
            current_user.schedule_data[lower_days[day]][str(period)]['start_time'] = "00:00"
            current_user.schedule_data[lower_days[day]][str(period)]['end_time'] = "00:00"
            current_user.schedule_data[lower_days[day]][str(period)]['times'] = ''
            current_user.schedule_data[lower_days[day]][str(period)]['subject'] = ''
            data = data.split(' ')
            data.remove(str(current_user.id))
            setattr(period_data, lower_days[day], ' '.join(data))
        
        flag_modified(current_user,'schedule_data')
        db.session.commit()
        redirect(url_for('scheduler'))
    #reads the schedule data from the db
    schedule = current_user.schedule_data
    periods = [[0 for _ in range(9)] for _ in range(5)]
    period_data = {495 + i*45:i for i in range(1,10)}
    for j,day in enumerate(lower_days):
        for period in range(1,10):
            current = schedule[day][str(period)]
            start1,end1 = current['start_time'],current['end_time']
            start,end = current['start_time'].split(':'),current['end_time'].split(':')
            start = int(start[0]) * 60 + int(start[1])
            end = int(end[0]) * 60 + int(end[1])
            if not end or not start:continue
            for period in period_data.keys():
                if period >= end:
                    periods[j][period_data[period] - 1] = (start1,end1)
                    break

    return render_template('scheduler.html',booked_periods=periods)

@app.route('/delete_session/<session_id>/<type>')
def delete_session(session_id,type):
    session = Session.query.get(session_id)
    if type != "1" or session.tutor_form_completed and session.student_form_completed:
        user = User.query.get(session.tutor)
        date = date_to_day(session.date.strftime('%Y-%m-%d'))
        user.schedule_data[date][str(session.period)]['times'] = user.schedule_data[date][str(session.period)]['times'].replace(session.date.strftime('%Y-%m-%d'), "")
        if type != "1":
            if session.tutor == current_user.id:
                other_user = User.query.get(session.student)
            else:
                other_user = User.query.get(session.student)
            temp = other_user.notifaction_data['deleted']
            other_user.notifaction_data['deleted'] = temp + [f'{user.username} canceled their session with you on {session.date} at {str(session.start_time)[:-3]}']
            flag_modified(other_user, "notifaction_data")
        db.session.delete(session)
        flag_modified(user,'schedule_data')
        db.session.commit()
        flash('Session Deleted', 'success')
    else:
        flash('Tutor and Student Forms not Complete', 'warning')
    return redirect(url_for('index'))

@app.route('/session_manager', methods = ['POST','GET'])
def session_manager():
    #use a 2d list that maps from a dictionary for each day and period, and then access
    users = []
    day = None
    date = None
    period = ''
    if request.method == 'POST':
        type = request.form.get('type')
        period = request.form.get('period')
        date = request.form.get('date')
        subject = request.form.get('subject')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        day = date_to_day(date)
        period_data = Periods.query.get(period)
        if type == '1': # if user is creating a new session
            user = current_user
            data = getattr(period_data, day, 'default')
            #Check that the times are correct
            period_start = 450 + int(period)*45
            period_end = period_start + 41
            # time_to_min(end_time) > time_to_min(start_time)
            if not (period_start <= time_to_min(start_time) or time_to_min(start_time) <= period_end or period_start <= time_to_min(end_time) or time_to_min(end_time) <= period_end):
                flash('invalid times', 'warning')
                return redirect(url_for('session_manager'))
            setattr(period_data, day, data + ' ' + str(user.id))
            user.schedule_data[day][str(period)]['start_time'] = str(start_time)
            user.schedule_data[day][str(period)]['end_time'] = str(end_time)
            user.schedule_data[day][str(period)]['subject'] = str(subject)
            flag_modified(user, 'schedule_data')
            db.session.commit()
        elif type == '0': # if user is looking up a session
            data = getattr(period_data, day, '')
            user_ids = data.split(' ')
            for id in user_ids:
                user = User.query.get(id)
                users.append(user)
        
    return render_template('session_manager.html', users = users[1:], day = day, date = date, period = str(period))

def string_to_time(time_str):
    hour, minute = map(int, time_str.split(':'))
    # Create a time object with the provided hour and minute
    result_time = time(hour=hour, minute=minute)
    return result_time
    
@app.route('/book_session/<id>/<date>/<period>')
def book_session(id, date, period):
    user = User.query.get(id)
    current = current_user.id

    day = date_to_day(date)
    data = user.schedule_data[day][period]
    current_user_id = current_user.get_id()
    people = {id:'',current_user_id:''}
    conversation = MessageHistory(
        people=people
    )
    db.session.add(conversation)
    db.session.commit()
    new_session = Session(
        tutor = id,
        start_time = string_to_time(data['start_time']),
        end_time = string_to_time(data['end_time']),
        student = current_user_id,
        period = period,
        # subject = data['subject'],
        date = datetime.strptime(date, '%Y-%m-%d').date(),
        message_history_id = 1
    )
    db.session.add(new_session)
    db.session.commit()
    people = {0:{'user':user,'id':''},0:{'user':current,'id':''}}
    conversation = MessageHistory(
        people=people,
    )
    
    other_user = User.query.get(id)
    temp = other_user.notifaction_data['deleted']
    other_user.notifaction_data['deleted'] = temp + [f'{user.username} booked a session with you on {new_session.date} at {str(new_session.start_time)[:-3]}']
    flag_modified(other_user, 'notifaction_data')
    
    user.schedule_data[day][period]['times'] += ' ' + str(date)
    flag_modified(user, 'schedule_data')
    db.session.add(conversation)
    db.session.commit()
    flash('Booked Session', 'success')
    return redirect(url_for('index'))

@app.route('/profile',methods=['POST','GET'])
def profile():
    if request.method == 'POST':
        #gets the values
        name = request.form.get("name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        username = request.form.get("username")

        #sets the values
        current_user.name=name,
        current_user.last_name=last_name,
        current_user.email=email,
        current_user.username=username,
        current_user.set_password(password)

        # Save the new user to the database
        db.session.commit()

    return render_template('profile.html',user = current_user)

@app.route('/charts')
def charts():
    return render_template('template_pages/charts.html')

@app.route('/forgot_password')
def forgot_password():
    return render_template('user_handling/forgot_password.html')

@app.route('/buttons')
def buttons():
    return render_template('template_pages/buttons.html') 

@app.route('/cards')
def cards():
    return render_template('template_pages/cards.html')

@app.route('/tables')
def tables():
    return render_template('template_pages/tables.html') 

@app.route('/utilities-animation')
def utilities_animation():
    return render_template('template_pages/utilities-animation.html') 

@app.route('/utilities-border')
def utilities_border():
    return render_template('template_pages/utilities-border.html') 

@app.route('/utilities-color')
def utilities_color():
    return render_template('template_pages/utilities-color.html') 

@app.route('/utilities-other')
def utilities_other():
    return render_template('template_pages/utilities-other.html') 

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.secret_key = "ben_sucks"  # Change this to a random, secure key
    socketio.run(app)