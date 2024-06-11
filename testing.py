from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
db = SQLAlchemy(app)

# Base User class
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verification_token = db.Column(db.String(255))
    schedule_data = db.Column(db.JSON, default=lambda: {})
    notification_data = db.Column(db.JSON, default=lambda: {})
    sessions = db.relationship('Session', backref='user', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)
    hours_of_service = db.Column(db.Float, default=0.0)
    status = db.Column(db.String, default='')
    image_data = db.Column(db.LargeBinary)
    qualification_data = db.Column(db.JSON, default=lambda: {})
    volunteer_hours = db.Column(db.JSON, default=lambda: {})
    user_type = db.Column(db.String(50))  # To differentiate user types

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Admin class
class Admin(User):
    admin_level = db.Column(db.String(50), default='Super Admin')  # Unique attribute

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

    def promote_user(self, user):
        # Example method unique to Admin
        print(f'User {user.username} promoted by {self.username}')

# Regular User class
class RegularUser(User):
    __mapper_args__ = {
        'polymorphic_identity': 'regular_user',
    }

    def use_feature(self):
        # Example method unique to RegularUser
        print(f'User {self.username} is using a regular feature')

# Buyer class
class Buyer(RegularUser):
    purchase_history = db.Column(db.JSON, default=lambda: [])  # Unique attribute

    __mapper_args__ = {
        'polymorphic_identity': 'buyer',
    }

    def buy_item(self, item):
        # Example method unique to Buyer
        print(f'Buyer {self.username} purchased {item}')
        self.purchase_history.append(item)

# Seller class
class Seller(RegularUser):
    items_for_sale = db.Column(db.JSON, default=lambda: [])  # Unique attribute

    __mapper_args__ = {
        'polymorphic_identity': 'seller',
    }

    def list_item(self, item):
        # Example method unique to Seller
        print(f'Seller {self.username} listed {item} for sale')
        self.items_for_sale.append(item)

# Example Models for Session and Feedback
class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255))

# Create the database and tables
with app.app_context():
    db.create_all()

# Adding sample records for testing
with app.app_context():
    if not User.query.first():
        admin = Admin(username='admin', name='Admin', last_name='User', email='admin@example.com')
        admin.set_password('adminpassword')
        db.session.add(admin)

        buyer = Buyer(username='buyer', name='Buyer', last_name='User', email='buyer@example.com')
        buyer.set_password('buyerpassword')
        db.session.add(buyer)

        seller = Seller(username='seller', name='Seller', last_name='User', email='seller@example.com')
        seller.set_password('sellerpassword')
        db.session.add(seller)

        db.session.commit()
