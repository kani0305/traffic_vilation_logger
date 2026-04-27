from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Violation

import os
import qrcode

from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from twilio.rest import Client


# 🚀 APP SETUP
app = Flask(__name__)

app.config['SECRET_KEY'] = 'traffic_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 📸 UPLOAD CONFIG FIX
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

QR_FOLDER = "static/qr_codes"
os.makedirs(QR_FOLDER, exist_ok=True)

db.init_app(app)


# 🔐 LOGIN SETUP
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 🏗️ CREATE DB
with app.app_context():
    db.create_all()


# 🏠 DASHBOARD
@app.route('/')
@login_required
def home():

    total = Violation.query.count()
    paid = Violation.query.filter_by(status="Paid").count()
    unpaid = Violation.query.filter_by(status="Unpaid").count()

    return render_template("dashboard.html",
                           total=total,
                           paid=paid,
                           unpaid=unpaid)


# 🔐 LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')

        return "❌ Invalid Login"

    return render_template("login.html")


# 🚪 LOGOUT
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# ➕ ADD VIOLATION (🔥 FIXED IMAGE + PHONE + SMS)
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_violation():

    if request.method == 'POST':

        vehicle = request.form['vehicle_number']
        phone = request.form['phone']
        violation = request.form['violation_type']
        location = request.form['location']
        fine = request.form['fine_amount']

        # 📸 IMAGE FIX
        image_file = request.files.get('image')
        filename = None

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(UPLOAD_FOLDER, filename))

        # 💾 SAVE TO DB
        v = Violation(
            vehicle_number=vehicle,
            phone=phone,
            violation_type=violation,
            location=location,
            fine_amount=fine,
            image=filename
        )

        db.session.add(v)
        db.session.commit()

        # 🔳 QR CODE
        qr_url = url_for('status', id=v.id, _external=True)
        img = qrcode.make(qr_url)
        img.save(os.path.join(QR_FOLDER, f"{v.id}.png"))

        # 📱 SMS
        send_sms(phone,
                 f"""
🚨 Traffic Violation Notice

Vehicle: {vehicle}
Violation: {violation}
Location: {location}
Fine: ₹{fine}

Status: Unpaid
""")

        return "Violation Added & SMS Sent"

    return render_template("add_violation.html")


# 📋 VIEW
@app.route('/view')
@login_required
def view():

    data = Violation.query.order_by(Violation.id.desc()).all()
    return render_template("view_violations.html", data=data)


# 💰 PAY
@app.route('/pay/<int:id>')
@login_required
def pay(id):

    v = Violation.query.get_or_404(id)
    v.status = "Paid"
    db.session.commit()

    send_sms(
        v.phone,
        f"""
✅ Payment Received

Vehicle: {v.vehicle_number}
Amount: ₹{v.fine_amount}
Status: Paid

Thank you!
"""
    )

    return redirect('/view')


# 🔍 STATUS
@app.route('/status/<int:id>')
def status(id):

    v = Violation.query.get_or_404(id)
    return render_template("status.html", v=v)


# 📱 SMS FUNCTION (SAFE)
def send_sms(to, message):

    try:
        account_sid = "ACb0a0bba0235482aac313739a3c122a63"
        auth_token = "c036fd2ad8469f1c3733af1f6e170a27"

        client = Client(account_sid, auth_token)

        client.messages.create(
            body=message,
            from_="+19783070470",
            to=to
        )

        print("SMS sent")

    except Exception as e:
        print("SMS error:", e)


# ▶️ RUN
if __name__ == "__main__":
    app.run(debug=True)