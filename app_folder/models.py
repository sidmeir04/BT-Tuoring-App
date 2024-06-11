from .extensions import db
from .load_jsons import *
from flask_login import UserMixin
from sqlalchemy import JSON
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255),unique=True)
    name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verification_token = db.Column(db.String(255))
    schedule_data = db.Column(JSON, default=load_default_schedule)
    notifaction_data = db.Column(JSON, default=load_default_notifactions)
    sessions = db.relationship('Session', backref='user', lazy = True)
    feedbacks = db.relationship('Feedback', backref='user', lazy = True)
    hours_of_service = db.Column(db.Float, default = 0.0)
    status = db.Column(db.String, default='')
    image_data = (db.Column(db.LargeBinary))
    qualification_data = db.Column(JSON,default=current_classlist)
    volunteer_hours = db.Column(JSON,default=load_volunteer_hour_json_file)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MessageHistory(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    people = db.Column(JSON, default=load_basic_json_file)
    messages = db.Column(JSON, default=load_non_basic_json_file)
    missed = db.Column(JSON, default=load_basic_json_file)
    session = db.relationship('Session', backref='message_history', lazy = True)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    date = db.Column(db.Date)
    start_date = db.Column(db.Date)
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