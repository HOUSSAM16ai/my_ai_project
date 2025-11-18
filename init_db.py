from app import create_app, db
from app.models import User

app = create_app("dev")

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Creating admin user...")
    # Create an admin user for testing
    admin_user = User(full_name="Admin User", email="benmerahhoussam16@gmail.com", is_admin=True)
    admin_user.set_password("1111")
    db.session.add(admin_user)
    db.session.commit()
    print("Database initialized successfully.")
