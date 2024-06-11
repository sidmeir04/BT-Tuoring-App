from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_login import LoginManager

db = SQLAlchemy()
socketio = SocketIO()
mail = Mail()
login_manager = LoginManager()
