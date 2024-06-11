from flask import Blueprint, render_template
from .extensions import db
from flask_login import login_required, current_user, login_user, logout_user
from flask import flash, redirect, url_for, render_template, request, jsonify
from sqlalchemy.orm.attributes import flag_modified
from .models import *
from .email import send_verification_email_to
from .wrappers import email_verified_required
import base64
from io import BytesIO


bp = Blueprint('main', __name__)



@bp.route('/verify_email/<token>')
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

@bp.route('/send_verification_email',methods=['POST'])
@login_required
def send_verification_email():
    if current_user.email_verification_token:
        send_verification_email_to(current_user)
        flash("A new verification email has been sent.", "info")
        return redirect(url_for('profile'))
    else:
        flash("Your email is already verified.", "info")
    return redirect(url_for('index'))

@bp.route('/appointment_details')
@login_required
@email_verified_required
def user_messages():
    #gets the session currently being viewed
    ID = request.args.get('identification')
    open_session = Session.query.get(ID)
    #gets the message history associated with the session
    message_history = MessageHistory.query.get(open_session.message_history_id)

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




@bp.route('/welcome')
def welcome():
    return render_template('welcome.html')

@bp.route('/delete_notification', methods=['POST'])
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
@bp.route('/index.html')
def reroute_user():
    return redirect(url_for('index'))

@bp.route("/")
@login_required
@email_verified_required
def index():
    #redirects if not logged
    if not current_user or not current_user.is_authenticated:return redirect(url_for('login'))

    # if current_user.role == 2:
    #     return render_template('index2.html')
    def replace_with_username(thing):
            if thing == None:return thing
            username = User.query.get(thing[1]["sender"]).username
            thing[1]["sender"] = username
            return thing
    
    sessions_where_teach = Session.query.filter_by(tutor=current_user.id,tutor_form_completed = False).all()
    if sessions_where_teach:
        sessions_where_teach_MH = [MessageHistory.query.get(session.message_history_id) for session in sessions_where_teach]
        sessions_where_teach_MH = list(map(lambda x: (x.missed['total'] - x.missed[str(current_user.id)],x.messages['list'][-1] if x.messages['list'] else None),sessions_where_teach_MH))
        sessions_where_teach_MH = [i if i != (0,None) else None for i in sessions_where_teach_MH]
        sessions_where_teach_PP = [base64.b64encode(User.query.get(i[1]['sender']).image_data).decode('utf-8') if i and User.query.get(i[1]['sender']).image_data else None for i in sessions_where_teach_MH]
        sessions_where_teach_MH = list(map(lambda x: replace_with_username(x),sessions_where_teach_MH))


    sessions_where_learn = Session.query.filter_by(student=current_user.id, student_form_completed = False).all()
    if sessions_where_learn:
        sessions_where_learn_MH = [MessageHistory.query.get(session.message_history_id) for session in sessions_where_learn]
        sessions_where_learn_MH = list(map(lambda x: (x.missed['total'] - x.missed[str(current_user.id)],x.messages['list'][-1] if x.messages['list'] else None),sessions_where_learn_MH))
        print(sessions_where_learn_MH)
        sessions_where_learn_MH = [i if i != (0,None) else None for i in sessions_where_learn_MH]
        print(sessions_where_learn_MH)
        sessions_where_learn_PP = [base64.b64encode(User.query.get(i[1]['sender']).image_data).decode('utf-8') if i and User.query.get(i[1]['sender']).image_data else None for i in sessions_where_learn_MH]
        sessions_where_learn_MH = list(map(lambda x: replace_with_username(x),sessions_where_learn_MH))
        print(sessions_where_learn_MH)

    return render_template('index0.html',
                            enum = enumerate,
                            username = current_user.username,
                            sessions_where_teach = sessions_where_teach,
                            sessions_where_teach_MH = sessions_where_teach_MH if sessions_where_teach else None,
                            sessions_where_teach_PP = sessions_where_teach_PP if sessions_where_teach else None,
                            sessions_where_learn = sessions_where_learn,
                            sessions_where_learn_MH = sessions_where_learn_MH if sessions_where_learn else None,
                            sessions_where_learn_PP = sessions_where_learn_PP if sessions_where_learn else None,
                            )

@bp.route('/login',methods=['GET','POST'])
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

@bp.route('/logout',methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Logged out!','success')
    return redirect(url_for('login'))

@bp.route('/register', methods = ['POST','GET'])
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

@bp.route('/complete_session/<id>')
@login_required
@email_verified_required
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
    params = {'type': 0,'id': session.id}
    if current_user.id == session.tutor:
        params['type'] = 2
        return redirect(url_for('completion_form',**params))
    if current_user.id == session.student:
        params['type'] = 1
        return redirect(url_for('completion_form',**params))
    return redirect(url_for('index'))

@bp.route('/completion_form', methods = ['GET','POST'])
@login_required
@email_verified_required
def completion_form():
    type = request.args.get('type')
    id = request.args.get('id')
    if request.method == 'POST':
        understanding = request.form.get('personal_rating')
        on_time = request.form.get('on_time')
        review = request.form.get('message')
        session = Session.query.get(id)

        if int(type) == 1:review_for = session.tutor
        else:review_for = session.student

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

########################################################################################################################
            
            #the code bellow is incomplete. it needs a system in which it takes the session's start time, end time and then do the math for the numebr of weeks

##########################################################################################
            tutor = User.query.get(session.tutor)
            datetime1 = datetime.combine(datetime.today(), session.end_time)
            datetime2 = datetime.combine(datetime.today(), session.start_time)
            difference =  datetime1 - datetime2
            difference = difference.total_seconds()/3600
            tutor.hours_of_service += round(float(difference),2)
            tutor.volunteer_hours["approved_index"].append(0)
            tutor.volunteer_hours["breakdown"].append({"start_date":session.date, "end_date":datetime.today(),"hours":round(float(difference),2)})
            flag_modified(tutor,"volunteer_hours")
            db.session.commit()
            return redirect(f'/delete_session/{session.id}/1')
        return redirect(url_for('index'))
    return render_template('completion_form.html', type = type, id = id)

@bp.route('/one_pager')
def one_pager():
    return render_template('one_pager.html')

@bp.route('/show_feedback')
@login_required
@email_verified_required
def show_feedback():
    reviews = Feedback.query.filter_by(review_for = current_user.id)
    return render_template('show_feedback.html', reviews = reviews)

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
lower_days = ['monday','tuesday','wednesday','thursday','friday']
@bp.route('/find_session',methods=['GET','POST'])
@login_required
@email_verified_required
def find_session():
    users,user_names = [],[]
    day, date = None, None
    tutor_name = ''
    if request.method == 'POST':
        date = request.form.get('modal_date')
        period = request.form.get('period')
        tutor_name = request.form.get('specific_tutor')
        subject = request.form.get('subject')
        # send to the front end, use jinja if to only show the session if that tutor is assigned
        if period != '-1':
            # if the period is not specified
            data = Periods.query.get(int(period))
            if date:
                day = date_to_day(date)
                data = getattr(data, day, 'defualt')
                user_names = [(User.query.get(int(id)).username,int(id),period,date,User.query.get(int(id)).qualification_data) for id in data.split(' ')[1:]]
                users = [User.query.get(int(id)).schedule_data[day][period] for id in data.split(' ')[1:]]
            else:
                for day in lower_days:
                    day_data = getattr(data, day, 'defualt')
                    # adding data to existing lists, could probably be done with map
                    [user_names.append((User.query.get(int(id)).username,int(id),period,find_next_day_of_week(day),User.query.get(int(id)).qualification_data)) for id in day_data.split(' ')[1:]]
                    [users.append(User.query.get(int(id)).schedule_data[day][period]) for id in day_data.split(' ')[1:]]

        elif date:
            day = date_to_day(date)
            day_data = [getattr(Periods.query.get(i),day) for i in range(1,10)]
            for period,period_data in enumerate(day_data):
                if period_data:
                    # adding data to existing lists, could probably be done with map
                    [user_names.append((User.query.get(int(id)).username,int(id),period+1,date,User.query.get(int(id)).qualification_data)) for id in period_data.split(' ')[1:]]
                    [users.append(User.query.get(int(id)).schedule_data[day][str(period+1)]) for id in period_data.split(' ')[1:]]
        elif subject or tutor_name:
            for period in range(1,10):
                for temp in [(getattr(Periods.query.get(period), day, 'default'),day) for day in lower_days]:
                    for id in temp[0].split(' ')[1:]:
                        user = User.query.get(int(id))
                        [user_names.append((user.username,int(id),period,find_next_day_of_week(temp[1]),user.qualification_data))]
                        [users.append(user.schedule_data[temp[1]][str(period)])]
        else:
            pass
        return render_template('find_session.html', users = users, user_names = user_names, enumerate = enumerate,tutor_name=tutor_name.lower(),type=request.method,subject=subject)
    return render_template('find_session.html', enumerate = enumerate,tutor_name=tutor_name.lower(),type=request.method)


@bp.route('/scheduler',methods=['POST','GET'])
@login_required
@email_verified_required
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
            subject = request.form.get('subject')
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
            current_user.schedule_data[lower_days[day]][str(period)]['subject'] = subject
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

@bp.route('/delete_session/<session_id>/<type>')
@login_required
@email_verified_required
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

        #this deletes the message history. If you want to save it for later, we can do that
        message_history = MessageHistory.query.get(session.message_history_id)
        db.session.delete(message_history)

        flag_modified(user,'schedule_data')
        db.session.commit()
        flash('Session Deleted', 'success')
    else:
        flash('Tutor and Student Forms not Complete', 'warning')
    return redirect(url_for('index'))

@bp.route('/book_session/<id>/<date>/<period>')
@login_required
@email_verified_required
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
        end_time = string_to_time(data['end_time']),
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

@bp.route('/profile', methods = ['POST','GET'])
@login_required
def profile():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        if 'submit1' in request.form:
            email = request.form.get('email')
            name = request.form.get('name')
            username = request.form.get('username')
            last_name = request.form.get('last_name')
            user.email = email
            if username != user.username:
                pass

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
                           badges=badges
                           )

@bp.route('/choose_classes',methods=['GET','POST'])
@login_required
@email_verified_required
def choose_classes():
    if request.method == "POST":
        for a_class in UNIVERSAL_CLASSLIST['class_list']:
            current_user.qualification_data[a_class] = int(request.form.get(a_class) != None)
        flag_modified(current_user,'qualification_data')
        db.session.commit()
        flash("Qualifications changed successfully",'success')
    
    checked = ['''checked="yes"''' if current_user.qualification_data[i] else "" for i in current_user.qualification_data]
    return render_template('choose_classes.html',
                           available_classes=UNIVERSAL_CLASSLIST['class_list'],
                           checked=checked)

@bp.route('/forgot_password')
def forgot_password():
    return render_template('user_handling/forgot_password.html')

@bp.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404
