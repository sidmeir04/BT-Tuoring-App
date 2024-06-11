from flask_socketio import emit
from .models import *
from .extensions import socketio
from flask import request
from flask_login import current_user
import base64
from sqlalchemy.orm.attributes import flag_modified


@socketio.on("connect")
def handle_connect():
    current_user.status = request.sid
    db.session.commit()

@socketio.on("disconnect")
def handle_disconnect():
    pass


@socketio.on("user_join")
def handle_user_join(user_id,history_id):
    #gets the message history associated and updates the room id
    history = MessageHistory.query.get(history_id)
    history.people[user_id] = request.sid
    flag_modified(history,'people')
    db.session.commit()


@socketio.on("notify_update")
def handle_notify_update():
    pass

@socketio.on("new_chat_message")
def handle_new_message(message,sending_user_id,history_id,session_id):
    sending_user = User.query.get(sending_user_id)
    history = MessageHistory.query.get(history_id)
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
    history = MessageHistory.query.get(history_id)
    print(history.missed)
    history.missed[other_id] += 1
    # history.missed[str(current_user.id)] = history.missed['total']
    flag_modified(history,'missed')
    db.session.commit()

@socketio.on("delete_badge")
def handle_user_join(badge_id):
    current_user.qualification_data[badge_id] = 0
    flag_modified(current_user,'qualification_data')
    db.session.commit()