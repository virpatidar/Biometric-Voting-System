from flask import Flask,render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
from models import db, Vote, Candidate, User
from models import db
import pyotp
import random
import os
import sqlite3
import base64

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  
db.init_app(app)  

otp_store = {}

# Dummy database for fingerprint storage
fingerprint_db = {}
registered_fingerprints = {}



def get_db_connection():
    conn = sqlite3.connect('voting_system.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = sqlite3.connect('voting_system.db')
    cursor = conn.cursor()
    
    # Create Candidates Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    # Create Votes Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            aadhaar TEXT NOT NULL UNIQUE,
            mobile TEXT NOT NULL,
            candidate TEXT NOT NULL
        )
    ''')


    conn.commit()
    conn.close()
    print("Database initialized successfully!")

initialize_db()


# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Define Database Models
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

# class Candidate(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     votes = db.relationship('Vote', backref='candidate', lazy=True)

# class Vote(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     voter_aadhaar = db.Column(db.String(12), unique=True, nullable=False)
#     selected_candidate = db.Column(db.String(100), nullable=False)

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    aadhaar_number = db.Column(db.String(12), unique=True, nullable=False)
    mobile = db.Column(db.String(10), unique=True, nullable=False)  # ✅ Make sure mobile exists
    fingerprint_data = db.Column(db.Text, nullable=True)  # ✅ Store fingerprint data here


# Store Admin Credentials
admins = {
    "admin1": "password123",
    "admin2": "securepass456",
    "admin3": "admin789"
}

candidates = {}
results = {}

# Store Candidates & Votes
candidates = {}
votes = {}

# Create database tables
with app.app_context():
    db.create_all()

# Store OTPs temporarily
otp_storage = {}

# -------------------- ROUTES --------------------

# 1️⃣ Index Page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin_id = request.form["admin_id"]
        password = request.form["password"]

        # Check credentials from the `admins` dictionary
        if admin_id in admins and admins[admin_id] == password:
            session['admin'] = admin_id  # Store admin session
            session['admin_logged_in'] = True  # ✅ New Feature: Track admin login status
            return redirect(url_for("admin_panel"))  # Redirect to admin panel
        elif admin_id == "admin" and password == "admin123":  # ✅ New Feature: Hardcoded credentials
            session['admin'] = "admin"
            session['admin_logged_in'] = True
            return redirect(url_for("admin_results"))  # Redirect to results page
        else:
            return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")

@app.route('/admin_panel')
def admin_panel():
    conn = sqlite3.connect("voting_system.db")
    cursor = conn.cursor()
    
    # Fetch voting results
    cursor.execute("SELECT candidate, COUNT(*) FROM votes GROUP BY candidate")
    results = dict(cursor.fetchall())  # Convert to dictionary { 'Candidate1': 10, 'Candidate2': 7 }

    # Fetch individual vote records
    cursor.execute("SELECT name, aadhaar, candidate FROM votes")
    vote_records = [{'voter_name': row[0], 'aadhaar': row[1], 'candidate': row[2]} for row in cursor.fetchall()]

    conn.close()

    return render_template("admin_panel.html", results=results, vote_records=vote_records)


@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    if "admin" in session:
        candidate_name = request.form["candidate_name"]
        conn = get_db_connection()
        conn.execute('INSERT INTO candidates (name) VALUES (?)', (candidate_name,))
        conn.commit()
        conn.close()
        
        return redirect(url_for("admin_panel"))
    return redirect(url_for("admin_login"))

@app.route('/remove_candidate', methods=['POST'])
def remove_candidate():
    if "admin" in session:
        candidate_name = request.form["remove_candidate_name"]
        conn = get_db_connection()
        conn.execute('DELETE FROM candidates WHERE name = ?', (candidate_name,))
        conn.commit()
        conn.close()
        
        return redirect(url_for("admin_panel"))
    return redirect(url_for("admin_login"))

@app.route('/get_candidates', methods=['GET'])
def get_candidates():
    conn = get_db_connection()
    candidates = [row['name'] for row in conn.execute('SELECT name FROM candidates').fetchall()]
    conn.close()
    return jsonify(candidates)

# 6️⃣ Voting Page
@app.route('/voting', methods=['GET', 'POST'])
def voting():
    conn = get_db_connection()
    candidates = [row['name'] for row in conn.execute('SELECT name FROM candidates').fetchall()]
    conn.close()
    
    if request.method == 'POST':
        name = request.form['name']
        date_of_birth = request.form['date_of_birth']
        aadhaar = request.form['aadhaar']
        mobile = request.form['mobile']
        otp = request.form['otp']
        candidate = request.form['candidate']
        fingerprint = request.form['fingerprint']  # Get fingerprint data
        scan_fingerprint = request.form['scan_fingerprint']  # Scan fingerprint

        if session.get('otp') and str(session['otp']) == otp:
            if fingerprint == scan_fingerprint:  # Verify fingerprint match
               conn = get_db_connection()
               conn.execute('INSERT INTO votes (name, aadhaar, mobile, candidate, fingerprint, scan_fingerprint) VALUES (?, ?, ?, ?, ?, ?)', 
                         (name, aadhaar, mobile, candidate, fingerprint, scan_fingerprint))
               conn.commit()
               conn.close()
               return "Vote Successfully Casted!"
            else:
                return "Fingerprint Authentication Failed!"
        else:
            return "Invalid OTP!"
    
    return render_template('voting.html', candidates=candidates)


@app.route("/webauthn/challenge", methods=["GET"])
def get_challenge():
    """Generate a challenge for WebAuthn fingerprint authentication."""
    challenge = os.urandom(32)  # Generate a random challenge
    session["challenge"] = base64.b64encode(challenge).decode("utf-8")  # Store in session
    print(f"Generated challenge: {challenge}")

    return jsonify({"challenge": list(challenge)})

    
    
@app.route("/register_fingerprint", methods=["POST"])
def register_fingerprint():
    data = request.get_json()

    if not data or "fingerprint_data" not in data or "mobile" not in data:
        return jsonify({"success": False, "message": "Fingerprint data and mobile number are required"}), 400

    mobile = data["mobile"]

    user = Voter.query.filter_by(mobile=mobile).first()  # ✅ Use Voter model, not Vote
    if user:
        try:
            user.fingerprint_data = data["fingerprint_data"]
            db.session.commit()
            return jsonify({"success": True, "message": "Fingerprint registered successfully!"})
        except Exception as e:
            print("Error saving fingerprint:", str(e))
            return jsonify({"success": False, "message": "Database error!"}), 500

    return jsonify({"success": False, "message": "User not found"}), 404


@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    data = request.json  # Receiving JSON data
    print("Received Data:", data)  # Debugging

    name = data.get('name')
    aadhaar = data.get('aadhaar')
    mobile = data.get('mobile')
    candidate = data.get('candidate')

    # Debugging prints
    print(f"Name: {name}, Aadhaar: {aadhaar}, Mobile: {mobile}, Candidate: {candidate}")

    if not name or not aadhaar or not mobile or not candidate:
        return jsonify({'success': False, 'message': 'All fields are required'})

    try:
        conn = sqlite3.connect('voting_system.db', timeout=10)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO votes (name, aadhaar, mobile, candidate) VALUES (?, ?, ?, ?)", 
                       (name, aadhaar, mobile, candidate))
        conn.commit()

        return jsonify({'success': True, 'message': f'Vote received for: {candidate}', 'redirect': '/vote_success'})

    except sqlite3.IntegrityError as e:
        return jsonify({'success': False, 'message': 'Database error: ' + str(e)})

    finally:
        cursor.close()
        conn.close()


@app.route('/vote_success')
def vote_success():
    return render_template('vote_success.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    candidates = Candidate.query.all()  # Fetch all candidates

    if request.method == 'POST':
        candidate_id = request.form.get('candidate')

        if not candidate_id:
            return "Candidate selection required!", 400

        candidate = Candidate.query.get(candidate_id)
        if candidate:
            candidate.votes += 1  # Increment vote count
            db.session.commit()
            return redirect('/admin_results')  # Redirect to results page after voting

    return render_template("vote.html", candidates=candidates)

@app.route('/admin/results')
def admin_results():
    conn = sqlite3.connect('voting.db')  # Connect to your database
    cursor = conn.cursor()

    # Fetch candidate names and their vote counts
    query = """
    SELECT candidates.name, COUNT(votes.candidate_id) as vote_count
    FROM candidates
    LEFT JOIN votes ON candidates.id = votes.candidate_id
    GROUP BY candidates.id
    ORDER BY vote_count DESC;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    
    conn.close()
    return render_template('admin_results.html', results=results)

@app.route('/admin/result')
def admin_result():
    if 'admin_logged_in' not in session:
        return redirect('/admin/login')

    # Fetch and display results

# Send OTP Route
@app.route('/send_otp', methods=['GET'])
def send_otp():
    
    mobile = request.args.get('mobile')
    otp = random.randint(100000, 999999)
    session['otp'] = otp

    # Twilio Configuration
    account_sid = 'AC0780ec44df26059d372322b4a7647009'  # Replace with your Twilio SID
    auth_token = '8d535484268320d42285538fc1bd8a2c'  # Replace with your Twilio Auth Token
    twilio_number = '+18064911555'  # Your Twilio Phone Number
    
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f'Your OTP for voting is: {otp}',
        from_=twilio_number,
        to=f'+91{mobile}'  # Adjust country code as needed
    )
    return jsonify({'status': 'OTP Sent'})

@app.route('/verify_otp', methods=['GET'])
def verify_otp():
    entered_otp = request.args.get('otp')
    if 'otp' in session and str(session['otp']) == entered_otp:
        return jsonify({"verified": True, "message": "OTP Verified Successfully ✅"})
    return jsonify({"verified": False, "message": "Incorrect OTP ❌"})


@app.route('/show_result')  
def show_result():  
    if 'admin_logged_in' not in session:  
        return redirect(url_for('admin_login'))  # Redirects if admin is not logged in  
      
    return render_template('admin_result.html')


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

