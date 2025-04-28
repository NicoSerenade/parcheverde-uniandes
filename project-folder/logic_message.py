from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room

#modules import
import logic
import db_operator

#Inicialize Flask app and SocketIO

# Create a Flask application instance
socketio = SocketIO()

def create_app() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '12345678'
    socketio.init_app(app)
    
    @app.route('/')
    def index():
        return render_template('index_prueba_messages.html')

    return app




#Ejecute the app when the script is run directly
if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host = '0.0.0.0', port = 5001, debug = True) #Be must changed app.tun(app) in app.py