
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User

app = create_app()

def create_admin_user():
    """Creates an admin user for testing purposes."""
    with app.app_context():
        # Check if the user already exists
        if User.query.filter_by(email='admin@test.com').first():
            print("Admin user already exists.")
            return

        user = User(
            full_name='Admin User',
            email='admin@test.com',
            is_admin=True
        )
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        print("Admin user created successfully.")

if __name__ == "__main__":
    create_admin_user()
