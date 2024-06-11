from flask import Flask
from .extensions import db, socketio, mail, login_manager
from .auth import load_user


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
    app.config['SESSION_COOKIE_NAME'] = 'Session_Cookie'
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    app.config['SESSION_PERMANENT'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS '] = True
    app.secret_key = "ben_sucks"  # Change this to a random, secure key

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USE_TLS'] = False

    #this needs to change to a bergen.org email
    app.config['MAIL_USERNAME'] = "oscarjepsen2007@gmail.com"
    app.config['MAIL_PASSWORD'] = "agda kzab akxo blpa"
    app.config['MAIL_DEFAULT_SENDER'] = "oscarjepsen2007@gmail.com"

    db.init_app(app)
    socketio.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)


    with app.app_context():
        from .routes import bp as main_bp
        app.register_blueprint(main_bp)

        from .context import add_context_processors
        add_context_processors(app)

        db.create_all()

    return app
