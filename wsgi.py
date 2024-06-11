from app_folder import create_app
from app_folder import socketio

app = create_app()

if __name__ == '__main__':
    app.secret_key = 'ben_does_not_suck'
    socketio.run(app, port=5000)