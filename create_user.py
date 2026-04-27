from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()

    admin = User(
        username="admin",
        password=generate_password_hash("1234")
    )

    db.session.add(admin)
    db.session.commit()

print("✅ Admin created successfully")