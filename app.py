#import all of the imports in a seperate document
from all_imports import *

#imports all of the functions and some variabels for running the app
from json_file_loading import *

# socketio = SocketIO()
socketio = 1

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
app.config['SESSION_COOKIE_NAME'] = 'Session_Cookie'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_PERMANENT'] = False

db = SQLAlchemy(app)

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
    missed = db.Column(JSON, default=load_basic_json_file)
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/appointment_details')
def details():
    #gets the session currently being viewed
    ID = request.args.get('identification')
    open_sesssion = Session.query.get(ID)
    #gets the message history associated with the session
    message_history = MessageHistory.query.get(open_sesssion.message_history_id)
    message_history.missed[str(current_user.id)] = message_history.missed['total']
    flag_modified(message_history,'missed')
    db.session.commit()

    messages = message_history.messages['list']

    messages = [{'mine': True if i['sender'] == current_user.username else False,'message':i['message'],'sender':i['sender']}  for i in messages]

    return render_template('appointment_details.html',
                           session=open_sesssion,
                           thiss=current_user,
                           messages=messages)


@socketio.on("connect")
def handle_connect():
    print(request.sid)
    #here, there should be a code segment that clears the notifications of missed messages
    #socketio connecting indicates that the user has viewed their messages
    pass

@socketio.on("disconnect")
def handle_disconnect():
    print('Client disconnected')

@socketio.on("leave")
def l(number):
    print(number,'sldigfadsfgdsjfgdajhfagfadgfkflsahjdsfgjks')

@socketio.on("user_join")
def handle_user_join(user_id,history_id):
    #gets the message history associated and updates the room id
    history = MessageHistory.query.get(history_id)
    history.people[user_id] = request.sid
    flag_modified(history,'people')
    db.session.commit()

@socketio.on("new_message")
def handle_new_message(message,sending_user_id,history_id):
    sending_user = User.query.get(sending_user_id)
    history = MessageHistory.query.get(history_id)
    people = history.people
    choose = [i for i in people.keys()]
    print(choose)
    other = choose[0] if choose[0] != str(sending_user.id) else choose[1]
    #saves all messages to the database
    history.messages['list'].append({'message':message,'sender':sending_user.username})
    print()
    #updates the total amount of messages and the ones a person has recieved
    history.missed[sending_user_id] += 1
    history.missed['total'] += 1

    flag_modified(history,'missed')
    flag_modified(history,'messages')
    db.session.commit()
    if history.people[other]:
        emit("chat", {"message": message, "username": sending_user.username}, room=history.people[other])

@socketio.on('recieved_message')
def verify_message_actively_recieved(user_id,history_id):
    history = MessageHistory.query.get(history_id)
    history.missed[user_id] += 1
    flag_modified(history,'missed')
    db.session.commit()


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
def load_user(user_id):
    return User.query.get(int(user_id))

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
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    #redirects if not logged 
    if not current_user or not current_user.is_authenticated:return redirect(url_for('login'))
    session_where_teach = Session.query.filter_by(tutor=current_user.id,tutor_form_completed = False).all()

    sessions_where_learn = Session.query.filter_by(student=current_user.id, student_form_completed = False).all()
    all_sessions = sessions_where_learn+session_where_teach
    missed = [MessageHistory.query.get(session.message_history_id).missed for session in all_sessions]
    missed = list(map(lambda x: x['total'] - x[str(current_user.id)],missed))

    return render_template('index0.html',username=current_user.username,
                           sessions = session_where_teach, 
                            student_sessions = sessions_where_learn,
                            missed = missed
                            )

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
            # Handle email overlap
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
    params = {
        'type': 0,
        'id': session.id
    }
    if current_user.id == session.tutor:
        params['type'] = 2
        return redirect(url_for('completion_form',**params))
    if current_user.id == session.student:
        params['type'] = 1
        return redirect(url_for('completion_form',**params))
    return redirect(url_for('index'))

@app.route('/completion_form', methods = ['GET','POST'])
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

        other_user = User.query.get(review_for)
        temp = other_user.notifaction_data['deleted']
        other_user.notifaction_data['deleted'] = temp + [f'{other_user.username} gave you feedback']
        flag_modified(other_user,"notifaction_data")

        db.session.add(feedback)
        db.session.commit()

        if session.tutor_form_completed and session.student_form_completed:
            # delete the session and add community service hours to the user
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

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
lower_days = ['monday','tuesday','wednesday','thursday','friday']
@app.route('/find_session',methods=['GET','POST'])
def find_session():
    users,user_names = [],[]
    day, date = None, None
    tutor_name = ''

    if request.method == 'POST':
        date = request.form.get('modal_date')
        period = request.form.get('period')
        tutor_name = request.form.get('specific_tutor')
        # send to the front end, use jinja if to only show the session if that tutor is assigned
        subject = request.form.get('subject')
        if not tutor_name:
            tutor_name = ''

        if period != '-1':
            # if the period is not specified
            data = Periods.query.get(int(period))
            if date:
                day = date_to_day(date)
                data = getattr(data, day, 'defualt')
                user_names = [(User.query.get(int(id)).username,id,period,date) for id in data.split(' ')[1:]]
                users = [User.query.get(int(id)).schedule_data[day][period] for id in data.split(' ')[1:]]
            else:
                for day in lower_days:
                    day_data = getattr(data, day, 'defualt')
                    # adding data to existing lists, could probably be done with map
                    [user_names.append((User.query.get(int(id)).username,id,period,find_next_day_of_week(day))) for id in day_data.split(' ')[1:]]
                    [users.append(User.query.get(int(id)).schedule_data[day][period]) for id in day_data.split(' ')[1:]]

        elif date:
            day = date_to_day(date)
            day_data = [getattr(Periods.query.get(i),day) for i in range(1,10)]
            for period,period_data in enumerate(day_data):
                if period_data:
                    # adding data to existing lists, could probably be done with map
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
        print([i for i in request.form.items()])
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
            data.remove(' ' + str(current_user.id) + ' ')
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
        user = User.query.get(current_user.id)
        date = date_to_day(session.date.strftime('%Y-%m-%d'))
        user.schedule_data[date][str(session.period)]['times'] = user.schedule_data[date][str(session.period)]['times'].replace(session.date.strftime('%Y-%m-%d'), "")
        if type != "1":
            if session.tutor == current_user.id: other_user = User.query.get(session.student)
            else: other_user = User.query.get(session.tutor)
            other_user.notifaction_data['deleted'] = other_user.notifaction_data['deleted'] + [f'{user.username} canceled their session with you on {session.date} at {str(session.start_time)[:-3]}']
            flag_modified(other_user, "notifaction_data")
        db.session.delete(session)
        flag_modified(user,'schedule_data')
        db.session.commit()
        flash('Session Deleted', 'success')
    else:
        flash('Tutor and Student Forms not Complete', 'warning')
    return redirect(url_for('index'))

@app.route('/book_session/<id>/<date>/<period>')
def book_session(id, date, period):
    user = User.query.get(id)

    day = date_to_day(date)
    data = user.schedule_data[day][period]
    current_user_id = current_user.get_id()
    conversation = MessageHistory(
        people = {id:'',current_user_id:''},
        missed = {'total':0,id:0,current_user_id:0}

    )

    db.session.add(conversation)
    db.session.commit()
    new_session = Session(
        tutor = id,
        start_time = string_to_time(data['start_time']),
        end_time = string_to_time(data['end_timed']),
        student = current_user_id,
        period = period,
        # subject = data['subject'],
        date = datetime.strptime(date, '%Y-%m-%d').date(),
        message_history_id = conversation.id
    )
    
    db.session.add(new_session)
    db.session.commit()
    
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

@app.route('/forgot_password')
def forgot_password():
    return render_template('user_handling/forgot_password.html')

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.secret_key = "ben_sucks"  # Change this to a random, secure key
    socketio.run(app)