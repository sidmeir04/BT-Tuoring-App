#import all of the imports in a seperate document
from all_imports import *

#imports all of the functions and some variabels for running the app
from json_file_loading import *

socketio = SocketIO()

def create_app():
    #setup the basics of the app
    main = Blueprint("main", __name__)
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.register_blueprint(main)
    socketio.init_app(app)

    #returning the app
    return app

app = create_app()
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
app.config["SQLALCHEMY_BINDS"] = {
    "records_db": "sqlite:///records_library.db"
}
app.config['SESSION_COOKIE_NAME'] = 'Session_Cookie'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_PERMANENT'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = "ben_sucks"  # Change this to a random, secure key

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False

#this needs to change to a bergen.org email
app.config['MAIL_USERNAME'] = "oscarjepsen2007@gmail.com"
app.config['MAIL_PASSWORD'] = "agda kzab akxo blpa"
app.config['MAIL_DEFAULT_SENDER'] = "oscarjepsen2007@gmail.com"
mail = Mail(app)

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255),unique=True)
    name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verification_token = db.Column(db.String(255))
    schedule_data = db.Column(db.LargeBinary(8), default=b'\x00' * 8)
    notifaction_data = db.Column(JSON, default=load_default_notifactions)
    hours_of_service = db.Column(db.Float, default = 0.0)
    status = db.Column(db.String, default='')
    image_data = db.Column(db.LargeBinary)
    qualification_data = db.Column(JSON,default=current_classlist)
    volunteer_hours = db.Column(db.Integer,default=0)
    student_teacher_data = db.Column(JSON, default = load_student_teacher_JSON)
    role = db.Column(db.Integer, default = 0)
    marked = db.Column(db.Integer, default = 0)
    sessions = db.relationship('Session', backref='user', lazy = True)
    feedbacks = db.relationship('Feedback', backref='user', lazy = True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class ActiveMessageHistory(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    people = db.Column(JSON, default=load_basic_json_file)
    messages = db.Column(JSON, default=load_non_basic_json_file)
    missed = db.Column(JSON, default=load_basic_json_file)
    session = db.relationship('Session', backref='active_message_history', lazy = True)

class MessageLogs(db.Model):
    __bind_key__ = "records_db"
    id = db.Column(db.Integer, primary_key = True)
    people = db.Column(JSON, default=load_basic_json_file)
    messages = db.Column(JSON, default=load_non_basic_json_file)
    session = db.Column(db.Integer,nullable=False)

class SessionLog(db.Model):
    __bind_key__ = "records_db"
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    day_of_the_week = db.Column(db.Integer)
    date = db.Column(db.Date)
    start_date = db.Column(db.Date)
    subject = db.Column(db.String(255))
    tutor = db.Column(db.Integer, nullable = False) # Tutor's ID number
    student = db.Column(db.Integer, nullable = False)
    period = db.Column(db.Integer)
    cancel_reason = db.Column(db.Integer)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    day_of_the_week = db.Column(db.Integer)
    date = db.Column(db.Date)
    start_date = db.Column(db.Date)
    subject = db.Column(db.String(255))
    tutor = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False) # Tutor's ID number
    student = db.Column(db.Integer, nullable = False)
    period = db.Column(db.Integer)
    session_history = db.Column(JSON, default = load_session_history_JSON)
    message_history_id = db.Column(db.Integer, db.ForeignKey('active_message_history.id'))
    closed = db.Column(db.Boolean, default = False)
    recurring = db.Column(db.Boolean, default = False)
    
    # Relationship to SessionFile
    files = db.relationship('SessionFile', back_populates='session', cascade='all, delete-orphan')

class SessionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    day_of_the_week = db.Column(db.Integer)
    date = db.Column(db.Date)
    start_date = db.Column(db.Date)
    subject = db.Column(db.String(255))
    tutor = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False) # Tutor's ID number
    student = db.Column(db.Integer, nullable = False)
    period = db.Column(db.Integer)

class SessionFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    file_data = db.Column(db.LargeBinary)  # Storing the file content
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)

    # Relationship back to Session
    session = db.relationship('Session', back_populates='files')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exists = db.Column(db.Boolean, nullable=False)
    on_time = db.Column(db.Integer, nullable=True)
    understanding = db.Column(db.Integer, nullable=True)
    date = db.Column(db.String(255), nullable=True)
    review_text = db.Column(db.String(255), nullable=True)
    subject = db.Column(db.String(255), nullable=True)
    tutoring = db.Column(db.Boolean, nullable=True)
    review_for = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False) # Tutor's ID number
    review_from = db.Column(db.String(255), nullable = False)


class Periods(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    monday = db.Column(db.String(256), default = '')
    tuesday = db.Column(db.String(256), default = '')
    wednesday = db.Column(db.String(256), default = '')
    thursday = db.Column(db.String(256), default = '')
    friday = db.Column(db.String(256), default = '')

'''
Period Key
0 = Before School
1 = Period 4
2 = Period 5
3 = Period 6
4 = Period 7
5 = After School
'''
period_converter = {
    0:0,
    1:4,
    2:5,
    3:6,
    4:7,
    5:-1
}

# Convert an integer to a 64-bit binary string
def int_to_64bit_binary_string(value):
    return struct.pack('Q', value)  # 'Q' is for 64-bit unsigned integer

# Convert a 64-bit binary string back to an integer
def binary_string_to_int(binary_string):
    return struct.unpack('Q', binary_string)[0]

def int_to_byte_string(value):
    return value.to_bytes(8, byteorder='big')

# Flip the bit at position `bit_position` in the 64-bit binary string
def flip_bit(user_id:int, day:str, period:int):
    '''
    Changes users Schedule at specified position.
    Returns value of flipped bit.\n
    Day should be an int where Monday = 0\n
    Period should be a value from 0 to 5\n
    0 = Before School\n
    1 = Period 4\n
    2 = Period 5\n
    3 = Period 6\n
    4 = Period 7\n
    5 = After School
    '''
    print(day,period)
    user = User.query.get(user_id)
    pos = 8*day + period
    print(pos)
    binary_string = user.schedule_data
    value = binary_string_to_int(binary_string)
    mask = 1 << pos
    flipped_value = value ^ mask
    print(int_to_byte_string(flipped_value))
    user.schedule_data = int_to_byte_string(flipped_value)
    db.session.commit()
    return (flipped_value >> pos) & 1

def initialize_period_data():
    if not Periods.query.first():
        for _ in range(0,6):
            newThing = Periods()
            db.session.add(newThing)
        db.session.commit()

def temp_function_for_default_user_loading():
    if not User.query.first():
        user1 = User(
            username = "Student1",
            name = "Ben",
            last_name = "Lozzano",
            email = "benlozzano@gmail.com",
            email_verification_token=None,
            role = 0
        )
        user1.set_password("s")
        db.session.add(user1)
        db.session.commit()

        user2 = User(
            username = "Admin",
            name = "Ben2",
            last_name = "Lozzano2",
            email = "benloz25@bergen.org",
            email_verification_token=None,
            role = 3
        )
        user2.set_password("s")

        user3 = User(
            username = "Teacher",
            name = "Bean",
            last_name = "Lasanga",
            email = "bean_lasanga@gmail.com",
            email_verification_token=None,
            role = 2
        )
        user3.set_password("s")

        user4 = User(
            username = "NHS Student",
            name = "Bacon",
            last_name = "Burrido",
            email = "america@gmail.com",
            email_verification_token=None,
            # schedule_data=json.loads('''{"monday": {"1": {"start_time": "08:30", "end_time": "08:31", "times": " 2024-06-24", "subject": null}, "2": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "3": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "4": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "5": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "6": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "7": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "8": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "9": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "subject": ""}, "tuesday": {"1": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "2": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "3": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "4": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "5": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "6": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "7": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "8": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "9": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "subject": ""}, "wednesday": {"1": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "2": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "3": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "4": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "5": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "6": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "7": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "8": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "9": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "subject": ""}, "thursday": {"1": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "2": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "3": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "4": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "5": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "6": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "7": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "8": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "9": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "subject": ""}, "friday": {"1": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "2": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "3": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "4": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "5": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "6": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "7": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "8": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "9": {"start_time": "00:00", "end_time": "00:00", "times": ""}, "subject": ""}}'''),
            volunteer_hours=0,
            role = 1,
            qualification_data = json.loads('''{"Math": 1, "Algebra": 0, "Science": 0, "Chemistry": 0, "Gym": 0, "Geometry": 0, "Biomolecular Quantum Physics": 0, "English": 0}''')
        )

        user4.set_password("s")
        period1 = Periods.query.first()
        period1.monday = " 4"


        db.session.add(user2)
        db.session.add(user3)
        db.session.add(user4)
        db.session.commit()

def temp_admin_loading_delete_later():
    if not User.query.first():
        user1 = User(
            username = "Ms. Genicoff",
            name = "Sharon",
            last_name = "Genicoff",
            email = "shagen@bergen.org",
            email_verification_token=None,
            role = 1
        )
        user1.set_password("Demo1")
        db.session.add(user1)
        db.session.commit()

        user2 = User(
            username = "Mr. Pena",
            name = "Carlos",
            last_name = "Pena",
            email = "carpen@bergen.org",
            email_verification_token=None,
            role = 3
        )
        user2.set_password("Demo1")

        user3 = User(
            username = "Ms. Kendall",
            name = "Monet",
            last_name = "Kendall",
            email = "monken@bergen.org",
            email_verification_token=None,
            role = 3
        )
        user3.set_password("Demo1")

        user4 = User(
            username = "Ms. Mak",
            name = "Cynthia",
            last_name = "Mak",
            email = "cynmak@bergen.org",
            email_verification_token=None,
            role = 3,
        )
        user4.set_password("Demo1")


        db.session.add(user2)
        db.session.add(user3)
        db.session.add(user4)
        db.session.commit()

def add_new_session(tutor_id,student_id,date,period,start_time, end_time,request,repeating):
    year, month, temp_day = (int(i) for i in date.split('-'))
    dayNumber = weekday(year, month, temp_day)
    if request:
        new_session = SessionRequest(
            tutor = tutor_id,
            start_time = start_time,
            end_time = end_time,
            student = student_id,
            period = period,
            start_date = datetime.today(),
            day_of_the_week = dayNumber,
            date = datetime.strptime(date, '%Y-%m-%d').date()
        )

        db.session.add(new_session)

        other_user = User.query.get(id)
        temp = other_user.notifaction_data['deleted']
        other_user.notifaction_data['deleted'] = temp + [f'{other_user.username} has requested a session with you on {new_session.date} at {str(new_session.start_time)[:-3]}']
        flag_modified(other_user, 'notifaction_data')

    else:
        tutor = User.query.get(tutor_id)
        conversation = ActiveMessageHistory(
            people = {tutor_id:'',student_id:''},
            missed = {'total':0,tutor_id:0,student_id:0}
        )
        db.session.add(conversation)
        db.session.commit()

        new_session = Session(
            tutor = tutor_id,
            start_time = start_time,
            end_time = end_time,
            student = student_id,
            period = period,
            start_date = datetime.today(),
            day_of_the_week = dayNumber,
            date = datetime.strptime(date, '%Y-%m-%d').date(),
            message_history_id = conversation.id,
            recurring = repeating
        )

        db.session.add(new_session)

    db.session.commit()

def remove_session(session_id):
    session = Session.query.get(session_id)
    session_files = SessionFile.query.filter_by(session_id = session_id).all()
    message_history = ActiveMessageHistory.query.get(session.message_history_id)
    print(message_history)
    for files in session_files:
        db.session.delete(files)
    db.session.delete(message_history)
    db.session.delete(session)
    db.session.commit()


with app.app_context():
    db.create_all(bind_key=None)
    db.create_all(bind_key="records_db")
    initialize_period_data()
    # temp_admin_loading_delete_later()
    temp_function_for_default_user_loading()


def generate_verification_token():
    return secrets.token_urlsafe(16)

def send_verification_email_to(user):
    token = generate_verification_token()
    user.email_verification_token = token
    db.session.commit()
    verification_link = request.url_root + f"/verify_email/{token}"
    msg = Message("Verify Your Email!", recipients=[user.email])
    msg.body = f"Click the following link to verify your email: {verification_link}"
    mail.send(msg)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_profile_image():
    included_endpoints = ['index','find_session','user_messages','scheduler','profile',"admin_temp_route","tag_managing","user_managing","approve_hours","view","user_uploads"]

    # Get the current endpoint
    current_endpoint = request.endpoint

    # Check if the current endpoint is in the excluded list
    if current_endpoint not in included_endpoints:
        return {}

    # If not excluded, inject the profile image
    profile_image = base64.b64encode(current_user.image_data).decode('utf-8') if current_user.image_data else None
    return {'profile_image':profile_image}

def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.email_verification_token:
            return f(*args, **kwargs)
        else:
            flash("You need to verify your email to access this page.", "warning")
            return redirect(url_for('profile'))
    return decorated_function

def check_for_closed_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.marked:
            params = {"id":current_user.marked,"form":"0","cancel_reason":"4"}
            return redirect(url_for("complete_session",**params))
        return f(*args,**kwargs)
    return decorated_function


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role >= 2:
            return f(*args, **kwargs)
        else:
            flash("You do not have the authority to access this page.", "danger")
            return redirect(url_for('index'))
    return decorated_function

@app.route('/verify_email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    if user:
        user.email_verification_token = None  # Clear the token once it's used
        db.session.commit()
        flash("Your email has been verified!", "success")
        return redirect(url_for('login'))

    else:
        flash("Verification link is invalid or has expired.", "danger")
        return redirect(url_for('profile'))

@app.route('/send_verification_email',methods=['POST'])
@login_required
def send_verification_email():
    if current_user.email_verification_token:
        send_verification_email_to(current_user)
        flash("A new verification email has been sent.", "info")
        return redirect(url_for('profile'))
    else:
        flash("Your email is already verified.", "info")
    return redirect(url_for('index'))

@app.route('/appointment_messages')
@login_required
@email_verified_required
@check_for_closed_session
def user_messages():
    #gets the session currently being viewed
    ID = request.args.get('identification')
    open_session = Session.query.get(ID)
    #gets the message history associated with the session
    message_history = ActiveMessageHistory.query.get(open_session.message_history_id)

    message_history.missed[str(current_user.id)] = message_history.missed['total']
    flag_modified(message_history,'missed')
    db.session.commit()

    other = open_session.tutor if open_session.tutor != current_user.id else open_session.student
    other = User.query.get(other)

    my_image = base64.b64encode(current_user.image_data).decode('utf-8') if current_user.image_data else None
    other_image = base64.b64encode(other.image_data).decode('utf-8') if other.image_data else None

    other = other.username

    messages = message_history.messages['list']
    #the next line is a horribly inefficient bit of code, pls fix it
    messages = [{'mine': True if i['sender'] == current_user.id else False,'message':i['message'],'sender':User.query.get(i['sender']).username}  for i in messages]
    return render_template('user_messages.html',
                           recipient = other,
                           my_image=my_image,
                           other_image = other_image,
                           session=open_session,
                           thiss=current_user,
                           messages=messages)

@app.route("/appointment_overview",methods=["POST","GET"])
@login_required
@email_verified_required
@check_for_closed_session
def user_overview():
    ID = request.args.get("identification")
    if request.method == "POST":
        id = request.form["id"]
        return redirect(f'/terminate_session?identification={id}')
    open_session = Session.query.get(ID)
    other_user = User.query.get(open_session.tutor) if current_user.role == 0 else User.query.get(open_session.student)
    other_user_image = base64.b64encode(other_user.image_data).decode('utf-8') if other_user.image_data else None
    return render_template("user_overview.html",session=open_session,other=other_user,other_image = other_user_image,role=current_user.role)

@app.route("/appointment_preview",methods=["POST","GET"])
@login_required
@email_verified_required
@check_for_closed_session
def user_preview():
    ID = request.args.get("identification")
    if request.method == "POST":
        id = request.form["id"]
        if int(request.form.get("submit")):
            return redirect(url_for("confirm_appointment",id=id))
        return redirect(f'/delete_session/{id}?pre=1')
    open_session = SessionRequest.query.get(ID)
    other_user = User.query.get(open_session.tutor) if current_user.role == 0 else User.query.get(open_session.student)
    other_user_image = base64.b64encode(other_user.image_data).decode('utf-8') if other_user.image_data else None
    return render_template("user_preview.html",session=open_session,other=other_user,other_image = other_user_image,type=current_user.role)

@app.route('/appointment_uploads')
@login_required
@email_verified_required
@check_for_closed_session
def user_uploads():
    ID = request.args.get("identification")
    open_session = Session.query.get(ID)
    other = open_session.tutor if open_session.tutor != current_user.id else open_session.student
    other = User.query.get(other)
    my_image = base64.b64encode(current_user.image_data).decode('utf-8') if current_user.image_data else None
    other_image = base64.b64encode(other.image_data).decode('utf-8') if other.image_data else None

    other = other.username
    return render_template("user_uploads.html",
                           len = len,
                           recipient = other,
                           my_image=my_image,
                           other_image = other_image,
                           session=open_session,
                           thiss=current_user)

@app.route('/material_upload/<session_id>', methods = ['POST'])
def material_upload(session_id):
    session = Session.query.get(session_id)
    data = request.files.get('image')
    if not data:
        flash("Attatch a file first!","danger")
        return redirect(url_for('user_uploads',identification=session_id))
    file_data = data.read()
    filename = data.filename
    new_file = SessionFile(filename=filename, file_data=file_data, session=session)
    db.session.add(new_file)
    db.session.commit()
    flash("File added successfully","success")
    return redirect(url_for('user_uploads',identification=session_id))

@app.route('/display_file/<int:file_id>')
def display_file(file_id):
    file = SessionFile.query.get(file_id)
    if file.filename.endswith('.png'):
        return Response(file.file_data, mimetype='image/png')
    elif file.filename.endswith('.pdf'):
        return Response(file.file_data, mimetype='application/pdf')
    return redirect(url_for('user_uploads'))

@app.route('/download_file/<int:file_id>')
def download_file(file_id):
    file = SessionFile.query.get(file_id)
    return send_file(
        io.BytesIO(file.file_data),
        download_name=file.filename,
        as_attachment=True
    )

@socketio.on("connect")
def handle_connect():
    current_user.status = request.sid
    db.session.commit()


@socketio.on("user_join")
def handle_user_join(user_id,history_id):
    #gets the message history associated and updates the room id
    history = ActiveMessageHistory.query.get(history_id)
    history.people[user_id] = request.sid
    flag_modified(history,'people')
    db.session.commit()


@socketio.on("new_chat_message")
def handle_new_message(message,sending_user_id,history_id,session_id):
    sending_user = User.query.get(sending_user_id)
    history = ActiveMessageHistory.query.get(history_id)
    people = history.people
    choose = [i for i in people.keys()]
    other = choose[0] if choose[0] != str(sending_user.id) else choose[1]
    other = User.query.get(other)

    #saves all messages to the database
    history.messages['list'].append({'message':message,'sender':int(sending_user_id)})

    #updates the total amount of messages and the ones a person has recieved
    history.missed[sending_user_id] += 1
    history.missed['total'] += 1
    flag_modified(history,'missed')
    flag_modified(history,'messages')
    db.session.commit()
    if other.status:
        emit("chat", {"message": message,
                      "username": sending_user.username,
                      "image_data": base64.b64encode(current_user.image_data).decode('utf-8') if current_user.image_data else None,
                      "session_id":session_id}, room=other.status)
    else:pass

@socketio.on('recieved_chat_message')
def handle_recieved_chat_message(other_id,history_id):
    history = ActiveMessageHistory.query.get(history_id)
    print(history.missed)
    history.missed[other_id] += 1
    # history.missed[str(current_user.id)] = history.missed['total']
    flag_modified(history,'missed')
    db.session.commit()

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/delete_notification', methods=['POST'])
@login_required
@email_verified_required
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

@app.route('/user_managing', methods = ['POST','GET'])
@login_required
@email_verified_required
@admin_only
@check_for_closed_session
def user_managing():
    if request.method == 'POST':
        promoted_user = request.form.get('promoted_user')
        rank = request.form.get('role')
        user = User.query.get(int(promoted_user))
        user.role = int(rank)
        db.session.commit()

    people = User.query.all()
    people = [i for i in people if i.role < 3]
    return render_template('user_handling/user_managing.html',people=people)

@app.route('/tag_managing', methods = ['POST','GET'])
@login_required
@email_verified_required
@admin_only
@check_for_closed_session
def tag_managing():
    NHS_students = User.query.filter_by(role=1).all()
    return render_template('user_handling/tag_managing.html', NHSs=NHS_students)

@app.route("/")
@login_required
@email_verified_required
@check_for_closed_session
def index():
    #redirects if not logged

    if not current_user or not current_user.is_authenticated:return redirect(url_for('login'))

    def replace_with_username(thing):
            if thing == None:return thing
            username = User.query.get(thing[1]["sender"]).username
            thing[1]["sender"] = username
            return thing
    if current_user.role == 0 or current_user.role == 1:
        sessions_where_learn = Session.query.filter_by(student=current_user.id).all()
        if sessions_where_learn:
            sessions_where_learn_MH = [ActiveMessageHistory.query.get(session.message_history_id) for session in sessions_where_learn]
            sessions_where_learn_MH = list(map(lambda x: (x.missed['total'] - x.missed[str(current_user.id)],x.messages['list'][-1] if x.messages['list'] else None),sessions_where_learn_MH))
            sessions_where_learn_MH = [i if i != (0,None) else None for i in sessions_where_learn_MH]
            sessions_where_learn_PP = [base64.b64encode(User.query.get(i[1]['sender']).image_data).decode('utf-8') if i and User.query.get(i[1]['sender']).image_data else None for i in sessions_where_learn_MH]
            sessions_where_learn_MH = list(map(lambda x: replace_with_username(x),sessions_where_learn_MH))
            people_learn = list(map(lambda x: User.query.get(x.tutor),sessions_where_learn ))

        
        sessions_where_teach = Session.query.filter_by(tutor=current_user.id).all()
        if sessions_where_teach:
            sessions_where_teach_MH = [ActiveMessageHistory.query.get(session.message_history_id) for session in sessions_where_teach]
            sessions_where_teach_MH = list(map(lambda x: (x.missed['total'] - x.missed[str(current_user.id)],x.messages['list'][-1] if x.messages['list'] else None),sessions_where_teach_MH))
            sessions_where_teach_MH = [i if i != (0,None) else None for i in sessions_where_teach_MH]
            sessions_where_teach_PP = [base64.b64encode(User.query.get(i[1]['sender']).image_data).decode('utf-8') if i and User.query.get(i[1]['sender']).image_data else None for i in sessions_where_teach_MH]
            sessions_where_teach_MH = list(map(lambda x: replace_with_username(x),sessions_where_teach_MH))
            people_teach = list(map(lambda x: User.query.get(x.student),sessions_where_teach ))

        meetings = {
            'teacher': ['2024-06-01', '2024-06-10', '2024-06-20'],
            'peer_tutor': ['2024-06-05', '2024-06-15', '2024-06-25']
        }
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        def get_month_dates(year, month):
            first_day = datetime(year, month, 1)
            next_month = first_day.replace(day=28) + timedelta(days=4)
            last_day = next_month - timedelta(days=next_month.day)
            return [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
        dates = get_month_dates(current_year, current_month)


        sessions_where_teach = sessions_where_teach
        sessions_where_teach_MH = sessions_where_teach_MH if sessions_where_teach else []
        sessions_where_teach_PP = sessions_where_teach_PP if sessions_where_teach else []
        sessions_where_learn = sessions_where_learn
        sessions_where_learn_MH = sessions_where_learn_MH if sessions_where_learn else []
        sessions_where_learn_PP = sessions_where_learn_PP if sessions_where_learn else []
        people_where_teach = people_teach if sessions_where_teach else []
        people_where_learn=people_learn if sessions_where_learn else []



        return render_template('homepages/student.html',
                        enum = enumerate,
                        username = current_user.username,
                        meetings=meetings, dates=dates, year=current_year, month=current_month,
                        sessions_where_learn = sessions_where_learn + sessions_where_teach,
                        sessions_where_learn_MH = sessions_where_learn_MH + sessions_where_teach_MH,
                        sessions_where_learn_PP = sessions_where_learn_PP + sessions_where_teach_PP,
                        people_where_learn = people_where_learn + people_where_teach,
                        today=datetime.today().strftime('%Y-%m-%d'),
                        image_data = base64.b64encode(current_user.image_data).decode('utf-8') if current_user.image_data else None,
                        role = current_user.role
                        )
    to_approve = Session.query.filter_by(closed = True).all()
    return render_template("homepages/admin.html",username=current_user.username,enum=enumerate, to_approve = len(to_approve))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully!", "success")
            if not current_user.email_verification_token:
                return redirect(url_for('index'))

            return redirect(url_for('profile'))
        else: flash("Invalid credentials!","danger")
    return render_template("user_handling/login.html")

@app.route('/logout',methods=['POST'])
@login_required
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
        # Validate form data (add your own validation logic)
        if not (
            name
            and last_name
            and email
            and password
            and confirm_password
            and username
        ):
        # Handle invalid input
            flash("Please fill in all fields.", "danger")
            return render_template("user_handling/register.html")
        #handle if existing user
        user = User.query.filter_by(username=username).first()
        if user is not None:
            # Handle email overlap
            flash("User already exist! Try a different username", "danger")
            return render_template("user_handling/register.html")
        user = User.query.filter_by(email=email).first()
        if user is not None:
            # Handle email overlap
            flash("User already exist! Try a different email", "danger")
            return render_template("user_handling/register.html")
        if password != confirm_password:
            # Handle password mismatch
            flash("Passwords do not match.", "danger")
            return render_template("user_handling/register.html")

        new_user = User(
            name=name,
            last_name=last_name,
            email=email,
            username=username,
            email_verification_token=1
        )
        new_user.set_password(password)

        # Save the new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))
    return render_template("user_handling/register.html")

@app.route('/terminate_session',methods=['GET','POST'])
@login_required
@email_verified_required
def terminate_session():
    id = request.args.get("identification")
    old_session = Session.query.get(id)
    repeating = old_session.recurring
    current_user.marked = int(id)

    db.session.commit()
    if request.method == "POST":

        cancel_reason = request.form.get("cancel_reason")
        ##############################################################################################################################

        finished = int(request.form.get('had_class'))
        cancel_reason = 4 if not cancel_reason else cancel_reason
        ##############################################################################################################################

                                            # for final product, there needs to be a more reliable way to tell if class happened than this #

        ##############################################################################################################################

        params = {"repeat":request.form.get("repeating_session"),"id":id,"cancel_reason":cancel_reason}
        if request.form.get("repeating_session") == "1":
            add_new_session(tutor_id=old_session.tutor,student_id=old_session.student,date=find_next_day_of_week(['monday','tuesday','wednesday','thursday','friday'][old_session.day_of_the_week]),period = old_session.period,request=False,repeating=True)
        return redirect(url_for("complete_session",**params))

    return render_template('terminate_session.html',id=id,repeating=repeating)

@app.route('/complete_session')
@login_required
@email_verified_required
def complete_session():
    id = request.args.get("id")
    session = Session.query.get(id)
    # fill_form = int(request.args.get('form'))

    session_log = SessionLog(
        tutor = session.tutor,
        student = session.student,
        cancel_reason = int(request.args.get("cancel_reason")),
        start_time = session.start_time,
        end_time = session.end_time,
        day_of_the_week = session.day_of_the_week,
        date = session.date,
        start_date = session.start_date,
        subject = session.subject,
        period = session.period
    )
    db.session.add(session_log)

    tutor = User.query.get(session.tutor)
    student = User.query.get(session.student)

    
    db.session.commit()

    # delete the session and add community service hours to the user

########################################################################################################################
    
    #The code need to be abnle to check for the time of start and time of end as well as the date            
    #what are you talking about? - Oscar

##########################################################################################
    tutor = User.query.get(session.tutor)
    datetime1 = datetime.combine(datetime.today(), session.end_time)
    datetime2 = datetime.combine(datetime.today(), session.start_time)
    difference =  datetime1 - datetime2
    difference = difference.total_seconds()/3600

    total_days = count_weekdays_between(session.start_date,datetime.today(),session.day_of_the_week)

##########################################################################################

        # Put in the if statement in the final product

##########################################################################################

    # if total_days > 0:
    if True:
        tutor.hours_of_service += round(float(difference),2)
        tutor.volunteer_hours["approved_index"].append(0)
        tutor.volunteer_hours["breakdown"].append({"start_date":session.start_date.strftime("%B %d, %Y"), "end_date":datetime.today().strftime("%B %d, %Y"),"hours":round(float(difference) * total_days,2)})
        flag_modified(tutor,"volunteer_hours")
        db.session.commit()
    ##############################################################################################################################

                                        # add for final product #

    ##############################################################################################################################
    # date = session.date
    # today = datetime.now().date()
    # if date >= today:
    #     flash('Tutoring Session has not Happened yet', 'warning')
    #     return redirect(url_for('index'))
    # if current_user.id == session.student and int(request.args.get("form")):
    #     return redirect(url_for('completion_form',sid=session.id,fid=feedback.id))
    flash("Session completed successfully",'success')
    return redirect(f"/delete_session/{id}?post=1")

@app.route('/one_pager')
def one_pager():
    return render_template('one_pager.html')

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
lower_days = ['monday','tuesday','wednesday','thursday','friday']
@app.route('/find_session',methods=['GET','POST'])
@login_required
@email_verified_required
@check_for_closed_session
# options=options,    options = load_available_classes()

def find_session():
    day, date = None, None
    tutor_name = ''
    options = load_available_classes()
    if request.method == 'POST':
        date = request.form.get('modal_date')
        period = request.form.get('period')
        tutor_name = request.form.get('specific_tutor')
        subject = request.form.get('subject')
        results = []
        if period != '-1':
            data = Periods.query.get(period)
            if date:
                day = date_to_day(date)
                data = getattr(data, day, 'defualt').strip()
                if data:
                    for user_id in data.split(' '):
                        user = User.query.get(user_id)
                        if user.qualification_data[subject]:
                            results.append([user.username,period,date,user_id])
            else:
                for day in lower_days:
                    day_data = getattr(data, day, 'defualt').strip()
                    if day_data:
                        for user_id in day_data.split(' '):
                            user = User.query.get(user_id)
                            if user.qualification_data[subject]:
                                results.append([user.username,period,find_next_day_of_week(day),user_id])
        # if period is not specified
        else:
            if date:
                day = date_to_day(date)
                for period in range(1,7):
                    for user_id in getattr(Periods.query.get(period), day, 'defualt').strip().split(' '):
                        user = User.query.get(user_id)
                        if user.qualification_data[subject]:
                            results.append([user.username,period,find_next_day_of_week(day),user_id])
            else:
                pass
                # Send message saying that you need to specify either date or time
        # send to the front end, use jinja if to only show the session if that tutor is assigned
        # if period != '-1':
        #     data = Periods.query.get(int(period))
        #     if date:
        #         day = date_to_day(date)
        #         data = getattr(data, day, 'defualt')
        #         user_names = [(User.query.get(int(id)).username,int(id),period,date,User.query.get(int(id)).qualification_data) for id in data.split(' ')[1:]]
        #         users = [User.query.get(int(id)).schedule_data[day][period] for id in data.split(' ')[1:]]
        #     else:
        #         for day in lower_days:
        #             day_data = getattr(data, day, 'defualt')
        #             # adding data to existing lists, could probably be done with map
        #             [user_names.append((User.query.get(int(id)).username,int(id),period,find_next_day_of_week(day),User.query.get(int(id)).qualification_data)) for id in day_data.split(' ')[1:]]
        #             [users.append(User.query.get(int(id)).schedule_data[day][period]) for id in day_data.split(' ')[1:]]

        # elif date:
        #     day = date_to_day(date)
        #     day_data = [getattr(Periods.query.get(i),day) for i in range(1,10)]
        #     for period,period_data in enumerate(day_data):
        #         if period_data:
        #             # adding data to existing lists, could probably be done with map
        #             [user_names.append((User.query.get(int(id)).username,int(id),period+1,date,User.query.get(int(id)).qualification_data)) for id in period_data.split(' ')[1:]]
        #             [users.append(User.query.get(int(id)).schedule_data[day][str(period+1)]) for id in period_data.split(' ')[1:]]
        # elif subject or tutor_name:
        #     for period in range(1,10):
        #         for temp in [(getattr(Periods.query.get(period), day, 'default'),day) for day in lower_days]:
        #             for id in temp[0].split(' ')[1:]:
        #                 user = User.query.get(int(id))
        #                 [user_names.append((user.username,int(id),period,find_next_day_of_week(temp[1]),user.qualification_data))]
        #                 [users.append(user.schedule_data[temp[1]][str(period)])]

        return render_template('find_session.html', results = results,tutor_name=tutor_name.lower(),type=request.method,subject=subject,options=options)
    

    

    return render_template('find_session.html', tutor_name=tutor_name.lower(),type=request.method,options=options)


@app.route('/scheduler',methods=['POST','GET'])
@login_required
@email_verified_required
@check_for_closed_session
def scheduler():
    if current_user.role < 1: return redirect(url_for('404'))
    if request.method == 'POST':
        thing = request.form.get('modalPass').split(',')
        period,day = int(thing[0]),thing[1]
        day = int(day)
        print('Scheduler:')
        print(period,day)
        period_data = Periods.query.get(period+1)
        data = getattr(period_data, lower_days[day], 'default')
        flip_bit(current_user.id,day,period)
        if ('delete', '') not in request.form.items():
            if str(current_user.id) not in getattr(period_data, lower_days[day], 'default').split(' '):
                setattr(period_data, lower_days[day], data + ' ' + str(current_user.id))

        else:
            data = data.split(' ')
            data.remove(' ' + str(current_user.id))
            setattr(period_data, lower_days[day], ' '.join(data))

        db.session.commit()
        redirect(url_for('scheduler'))
    num = int.from_bytes(current_user.schedule_data, byteorder='big')
    binary_str = f'{num:064b}'
    periods = []
    for i in range(0, 64, 8):
        row = [int(bit) for bit in binary_str[i:i+8]]
        periods.append(row)

    print(periods)
    return render_template('scheduler.html',booked_periods=periods)

@app.route('/delete_session/<session_id>')
@login_required
@email_verified_required
def delete_session(session_id):
    if not request.args.get("pre"):
        session = Session.query.get(session_id)

        user = User.query.get(session.tutor)
        
        db.session.delete(session)

        #this deletes the message history. If you want to save it for later, we can do that
        message_history = ActiveMessageHistory.query.get(session.message_history_id)

        db.session.delete(message_history)

        current_user.marked = 0

        if request.args.get("post"):
            flash('Session completed!', 'success')
            db.session.commit()
            return redirect(url_for("index"))
        if session.tutor == current_user.id: other_user = User.query.get(session.student)
        else: other_user = User.query.get(session.tutor)
        other_user.notifaction_data['deleted'] = other_user.notifaction_data['deleted'] + [f'{user.username} canceled their session with you on {session.date} at {str(session.start_time)[:-3]}']
        flag_modified(other_user, "notifaction_data")
        flash('Session cancelled!', 'success')
    else:
        session = SessionRequest.query.get(session_id)
        db.session.delete(session)
        db.session.commit()
        flash('Request Cancelled',"success")

    db.session.commit()
    return redirect(url_for('view_appointments'))

@app.route('/book_session/<id>/<date>/<period>')
@login_required
@email_verified_required
def book_session(id, date, period):
    user = User.query.get(id)

    day = date_to_day(date)
    year, month, temp_day = (int(i) for i in date.split('-'))
    dayNumber = weekday(year, month, temp_day)
    current_user_id = current_user.get_id()

    new_session = SessionRequest(
        tutor = id,
        start_time = string_to_time('00:00'),
        end_time = string_to_time('00:00'),
        student = current_user_id,
        period = period,
        start_date = datetime.today(),
        day_of_the_week = dayNumber,
        date = datetime.strptime(date, '%Y-%m-%d').date()
    )

    db.session.add(new_session)

    other_user = User.query.get(id)
    temp = other_user.notifaction_data['deleted']
    other_user.notifaction_data['deleted'] = temp + [f'{other_user.username} has requested a session with you on {new_session.date} at {str(new_session.start_time)[:-3]}']
    flag_modified(other_user, 'notifaction_data')

    db.session.commit()
    flash('Session requested!', 'success')
    return redirect(url_for('view_requests'))
    

@app.route('/teacher_dashboard', methods = ['POST','GET'])
@login_required
def teacher_dashboard():
    students = [User.query.get(id) for id in current_user.student_teacher_data['students']]
    if current_user.role != 2: return redirect(url_for('index'))
    return render_template('teacher_dashboard.html', students = students)

@app.route('/api/handle_button', methods=['POST'])
def handle_button():
    data = request.json
    parameter = data.get('parameter')
    # Process the parameter as needed
    response = {'message': f'Received parameter: {parameter}'}
    return jsonify(response)

@app.route('/teacher_manager', methods = ['GET','POST'])
def teacher_manager():
    teachers = User.query.filter_by(role=2).all()    
    return render_template('teacher_manager.html', teachers=teachers)

@app.route('/upload-roster/<int:teacher_id>', methods=['POST'])
def upload_roster(teacher_id):
    teacher = User.query.get(teacher_id)
    file = request.files['file']

    file_content = file.read().decode('utf-8')
    file_like_object = StringIO(file_content)
    csv_reader = csv.reader(file_like_object)
    header = next(csv_reader, None)
    if header is None or 'email' not in header:
        return jsonify({"error": "CSV file must contain an 'email' column"}), 400

    emails = [row[header.index('email')] for row in csv_reader]
    user_ids = db.session.query(User.id).filter(User.email.in_(emails)).all()
    user_ids = [user_id[0] for user_id in user_ids]

    teacher.student_teacher_data['students'] = user_ids
    flag_modified(teacher, 'student_teacher_data')
    db.session.commit()
    return redirect(url_for('teacher_manager'))

@app.route('/profile', methods = ['POST','GET'])
@login_required
@check_for_closed_session
def profile():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        if 'submit1' in request.form:
            email = request.form.get('email') if user.email_verification_token else user.email
            name = request.form.get('name')
            username = request.form.get('username')
            last_name = request.form.get('last_name')
            user.email = email

            user.username = username
            user.name = name
            user.last_name = last_name
            flash('Account information updated','success')
        elif 'submit2' in request.form:
            password = request.form.get('old_pass')
            if user.check_password(password):
                new_pass = request.form.get('new_pass')
                user.set_password(new_pass)
                flash('Your password has been updated!','success')
            else:
                flash('Current password is not correct', 'warning')
        else:
            data = request.files.get('image')
            img = Image.open(data.stream)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_square = make_square(img, size=300)
            buffered = BytesIO()
            img_square.save(buffered, format="JPEG")
            image_data = buffered.getvalue()
            user.image_data = image_data
            flash('Profile image changed!','success')
        db.session.commit()
    badges = [i if current_user.qualification_data[i] else None for i in current_user.qualification_data]
    return render_template('profile.html',
                           image_data=base64.b64encode(current_user.image_data).decode('utf-8') if current_user.image_data else None,
                           is_verified=current_user.email_verification_token != None,
                           badges=badges,
                           verified = current_user.email_verification_token == None
                           )

@socketio.on("change_badge")
def handle_user_join(badge_id,user):
    user = User.query.get(int(user))
    user.qualification_data[badge_id] = int(not user.qualification_data[badge_id])
    flag_modified(user,'qualification_data')
    db.session.commit()


@app.route('/choose_classes/<id>',methods=['GET','POST'])
@login_required
@email_verified_required
@admin_only
def choose_classes(id):
    user = User.query.get(int(id))
    if request.method == "POST":
        for a_class in UNIVERSAL_CLASSLIST['class_list']:
            user.qualification_data[a_class] = int(request.form.get(a_class) != None)
        flag_modified(user,'qualification_data')
        db.session.commit()
        flash("Qualifications changed successfully",'success')
    
    checked = ['''checked="yes"''' if user.qualification_data[i] else "" for i in user.qualification_data]
    return render_template('choose_classes.html',
                           available_classes=UNIVERSAL_CLASSLIST['class_list'],
                           checked=checked,
                           id = id)

@app.route('/view_appointments',methods=["GET","POST"])
@login_required
@email_verified_required
@check_for_closed_session
def view_appointments():

    session_requests_where_student = SessionRequest.query.filter_by(student=current_user.id).all()
    session_requests_where_tutor = SessionRequest.query.filter_by(tutor=current_user.id).all()

    confirmed_sessions_where_student = Session.query.filter_by(student=current_user.id, closed = False).all()
    confirmed_sessions_where_tutor = Session.query.filter_by(tutor=current_user.id, closed = False).all()

    return render_template("view_appointments.html",
                           type=current_user.role,
                           len=len,
                           session_requests_where_student=session_requests_where_student,
                           session_requests_where_tutor=session_requests_where_tutor,
                           confirmed_sessions_where_student=confirmed_sessions_where_student,
                           confirmed_sessions_where_tutor=confirmed_sessions_where_tutor)

@app.route('/view_requests',methods=["GET","POST"])
@login_required
@email_verified_required
@check_for_closed_session
def view_requests():
    if request.method == "POST":
        id = request.form["id"]
        if int(request.form.get("submit")):
            return redirect(url_for("confirm_appointment",id=id))
        if int(request.form.get("pre")):
            return redirect(f'/delete_session/{id}?pre=1')
        return redirect(f'/terminate_session?identification={id}')

    session_requests_where_student = SessionRequest.query.filter_by(student=current_user.id).all()
    session_requests_where_tutor = SessionRequest.query.filter_by(tutor=current_user.id).all()


    return render_template("view_requests.html",
                           type=current_user.role,
                           len=len,
                           session_requests_where_student=session_requests_where_student,
                           session_requests_where_tutor=session_requests_where_tutor)

@app.route('/confirm_appointment')
@login_required
@email_verified_required
def confirm_appointment():
    id = request.args.get('id')
    session_request = SessionRequest.query.get(id)
    tutor = User.query.get(session_request.tutor)
    student = User.query.get(session_request.student)
    add_new_session(tutor_id=session_request.tutor,student_id=student.id,date = session_request.date.strftime('%Y-%m-%d'),period = session_request.period,request=False,repeating=False)

    # temp = tutor.notifaction_data['deleted']
    # student.notifaction_data['deleted'] = temp + [f'{student.username} confirmed the session with you on {new_session.date} at {str(new_session.start_time)[:-3]}']
    # flag_modified(student, 'notifaction_data')
    db.session.delete(session_request)
    db.session.commit()
    flash("Session confirmed!","success")
    return redirect(url_for("view_appointments"))


@app.route("/view_details", methods = ['POST','GET'])
def view():
    id = request.args.get('id')
    session = Session.query.get(id)
    tutor_name = User.query.get(session.tutor)
    tutor_name = f"{tutor_name.name} {tutor_name.last_name}"
    student_name = User.query.get(session.student)
    student_name = f"{student_name.name} {student_name.last_name}"
    if request.method == 'POST':
        if request.form.get('action') == 'button1':
            tutor = User.query.get(session.tutor)
            tutor.volunteer_hours += ((datetime.combine(datetime.today(), session.end_time) - datetime.combine(datetime.today(), session.start_time)).total_seconds() / 60) * session.session_history['sessions']
            db.session.commit()
        remove_session(session.id)
        next_session = Session.query.filter_by(closed=True).all()
        if len(next_session) < 1:
            flash('All Hours Reviewed', 'success')
            return redirect(url_for('index'))
        else:
            flash('Student Hours Reviewed', 'success')
            return redirect(url_for('view', id = Session.query.filter_by(closed=True).all()[0].id))
    return render_template("view.html", student_name = student_name, tutor_name = tutor_name, session = session, hours = round(((datetime.combine(datetime.today(), session.end_time) - datetime.combine(datetime.today(), session.start_time)).total_seconds() / 3600) * session.session_history["sessions"],2))

@app.route("/create_request")
def create_request():
    return render_template("create_request.html")

@app.route("/session_hindsight",methods=["GET","POST"])
def session_hindsight():
    id = request.args.get("identification")
    if request.method == "POST":
        feedback = request.form.get("feedback_text")
        repeating = int(request.form.get("repeating_session"))
        session = Session.query.get(id)
        session.session_history['sessions'] += 1
        session.session_history['descriptions'].append(feedback)
        flag_modified(session, 'session_history')

        if repeating:
            pass
        else:
            session.closed = True
            
        db.session.commit()
        return redirect(url_for('index'))
    return render_template("session_hindsight.html",id=id)

@app.route("/admin_temp_route",methods=["POST","GET"])
def admin_temp_route():
    if request.method == "POST":
        from random import randint, sample

        number = int(request.form.get("number"))
        if number <= 0:
            flash("The number has to be above 0","danger")
            return render_template("admin_temp_route.html")
        
        if int(request.form.get("submit")):
            if len(User.query.filter_by(role=1).all()) == 0 or len(User.query.filter_by(role=0).all()) == 0:
                flash("Insert some students and tutors first","warning")
                return redirect(url_for("admin_temp_route"))
            available_filepaths = [
                "static/assets2/img/deleteTempImages/ec3b11a9e61917ff610aaf38a3b3a08f_18-02s06.png",
                "static/assets2/img/deleteTempImages/I3UzM.png",
                "static/assets2/img/deleteTempImages/Linear-function-example-sol-1.png",
                "static/assets2/img/deleteTempImages/material-U2f5naP5-thumb.png",
                "static/assets2/img/deleteTempImages/png-clipart-linear-subspace-linear-algebra-space-linear-map-system-of-linear-equations-a-linear-design-angle-rectangle-thumbnail.png",
                "static/assets2/img/deleteTempImages/Screen-Shot-2020-04-15-at-6.36.08-PM.png"
            ]
            session_reports = [
                "We covered the foundational concepts of calculus, specifically focusing on understanding derivatives and their applications. The student initially struggled with differentiating more complex functions, but after walking through several examples, they showed significant improvement. We also briefly touched on integration to preview what’s coming next.",
                "In today's session, we concentrated on solving linear equations and graphing them accurately. The student had a few misunderstandings regarding slope-intercept form, so we spent time clarifying that. We finished with some graphing exercises to reinforce the concepts and improve speed and accuracy.",
                "We discussed the structure of a strong argumentative essay, starting with crafting a compelling thesis statement. The student practiced outlining their ideas to support their thesis, and we went over how to transition between paragraphs. By the end of the session, they felt more confident in organizing their essays logically.",
                "We worked through quadratic equations, focusing on both the factorization and completing the square methods. Initially, the student found it hard to recognize when factorization was possible, but we broke it down step-by-step. After several practice problems, they became more comfortable identifying the correct method and solving efficiently.",
                "Today's session focused on study habits and time management skills. The student has been having difficulty balancing homework and upcoming tests, so we created a study schedule. We also discussed prioritization techniques and strategies for managing distractions."
            ]

            time_sets = [
                ("08:30","08:45",1),
                ("13:00","13:25",7),
                ("10:00","10:25",3),
                ("09:30","09:40",2),
                ("14:15","14:50",9)
            ]
            subjects = [
                "Mathematics",
                "English Literature",
                "Biology",
                "Chemistry",
                "Physics",
                "History",
                "Geography",
                "Foreign Language",
                "Physical Education",
                "Computer Science"
            ]


            for _ in range(number):
                tutor = sample(User.query.filter_by(role=1).all(),1)[0].id
                student = sample(User.query.filter_by(role=0).all(),1)[0].id

                user = User.query.get(tutor)
                date=find_next_day_of_week(sample(['monday','tuesday','wednesday','thursday','friday'],1)[0])
                year, month, temp_day = (int(i) for i in date.split('-'))
                dayNumber = weekday(year, month, temp_day)
                conversation = ActiveMessageHistory(
                    people = {tutor:'',student:''},
                    missed = {'total':0,tutor:0,student:0}
                )
                db.session.add(conversation)
                db.session.commit()

                num_sessions = randint(1,3)
                fake_history = {"descriptions": [session_reports[randint(0,4)] for _ in range(num_sessions)], "sessions": num_sessions}

                start_time,end_time,period = time_sets[randint(0,4)]

                new_session = Session(
                    tutor = tutor,
                    subject = subjects[randint(0,9)],
                    start_time = string_to_time(start_time),
                    end_time = string_to_time(end_time),
                    session_history = fake_history,
                    student = student,
                    period = period,
                    start_date = datetime.today(),
                    day_of_the_week = dayNumber,
                    date = datetime.strptime(date, '%Y-%m-%d').date(),
                    message_history_id = conversation.id,
                    recurring = False,
                    closed=True
                )

                db.session.add(new_session)
                tutor = User.query.get(tutor)
                db.session.commit()

                

                for _ in range(randint(1,8)):
                    relative_path = available_filepaths[randint(0,5)]

                    file_path = os.path.join(os.getcwd(), relative_path)


                    with open(file_path, 'rb') as file:
                        file_data = file.read()

                    filename = os.path.basename(file_path)

                    new_file = SessionFile(filename=filename, file_data=file_data, session=new_session)
                    db.session.add(new_file)
                    db.session.commit()
            
        else:
            role = request.form.get("role")
            first_names = [
                "Maria",     # Spanish/Latin
                "James",     # English
                "Sakura",    # Japanese
                "Amit",      # Indian
                "Liam",      # Irish
                "Fatima",    # Arabic
                "Chen",      # Chinese
                "Olga",      # Russian
                "Zara",      # Persian
                "David"      # Hebrew
            ]
            last_names = [
                "Garcia",    # Spanish
                "Smith",     # English
                "Nguyen",    # Vietnamese
                "Patel",     # Indian
                "Kowalski",  # Polish
                "Alvarez",   # Spanish
                "Olsen",     # Scandinavian
                "Kim",       # Korean
                "Hassan",    # Arabic
                "Ivanov"     # Russian
            ]
            num_users = len(User.query.all())
            for i in range(number):
                name = first_names[randint(0,9)]
                last_name = last_names[randint(0,9)]
                qual_data = {"Math": randint(0,1), "Algebra": randint(0,1), "Science": randint(0,1), "Chemistry": randint(0,1), "Gym": randint(0,1), "Geometry": randint(0,1), "Biomolecular Quantum Physics": randint(0,1), "English": randint(0,1)} if int(role) else {"Math": 0, "Algebra": 0, "Science": 0, "Chemistry": 0, "Gym": 0, "Geometry": 0, "Biomolecular Quantum Physics": 0, "English": 0}
                user = User(
                    username = "User" + str(num_users + i + 1),
                    name = name,
                    last_name = last_name,
                    email = f"{name[:3]}{last_name[:3]}{str(num_users + i + 1)}@bergen.org",
                    email_verification_token=None,
                    role = int(role),
                    qualification_data = qual_data
                )
                user.set_password("TotallyRandomPassword")
                db.session.add(user)
                db.session.commit()
    return render_template("admin_temp_route.html",student_num = len(User.query.filter_by(role=0).all()),tutor_num = len(User.query.filter_by(role=1).all()),session_num = len(Session.query.all()))
#dummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummydummy


@app.route('/approve_hours')
@login_required
@email_verified_required
@admin_only
def approve_hours():
    to_approve = Session.query.filter_by(closed = True).all()
    tutors = [User.query.get(i.tutor).name + ' ' + User.query.get(i.tutor).last_name for i in to_approve]
    hours_worth = [round(((datetime.combine(datetime.today(), i.end_time) - datetime.combine(datetime.today(), i.start_time)).total_seconds() / 3600) * i.session_history["sessions"],2) for i in to_approve]
        

    return render_template("approve_hours.html",hours_to_approve=to_approve,hours_worth = hours_worth, tutors=tutors)

@app.route('/calendar')
@login_required
@email_verified_required
def calendar():

    #replace these dartes with the actual meeting dates when done
    meetings = {
        'teacher': ['2024-08-01', '2024-08-30', '2024-08-20'],
        'peer_tutor': ['2024-08-04', '2024-08-15', '2024-08-25']
    }
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    def get_month_dates(year, month):
        first_day = datetime(year, month, 1)
        next_month = first_day.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        return [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
    dates = get_month_dates(current_year, current_month)
    return render_template('calendar.html',username = current_user.username,meetings=meetings, dates=dates, year=current_year, month=current_month,today=datetime.today().strftime('%Y-%m-%d'))

@app.route('/forgot_password')
def forgot_password():
    return render_template('user_handling/forgot_password.html')

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.secret_key = 'ben_does_not_suck'
    #add a host="" to run on capcitor with flask-socketio
    socketio.run(app, port = 5000)