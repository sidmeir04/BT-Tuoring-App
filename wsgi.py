from app import app
from app import socketio

if __name__ == '__main__':
    app.secret_key = 'ben_does_not_suck'
    socketio.run(app)