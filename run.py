# run.py
import os
from app import create_app

# Load the appropriate config based on the FLASK_CONFIG environment variable
config_name = os.getenv('FLASK_CONFIG') or 'config.DevelopmentConfig'
app = create_app(config_name)

if __name__ == '__main__':
    app.run()