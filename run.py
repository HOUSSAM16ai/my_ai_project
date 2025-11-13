# run.py - The Application Entry Point

import os

from app import create_app, socketio

# We get the environment from FLASK_ENV, defaulting to 'development'
config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    socketio.run(app, allow_unsafe_werkzeug=True)
