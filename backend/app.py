from flask import Flask, request, redirect, send_from_directory, jsonify
import sqlite3
import os

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "certificates")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__, static_folder=FRONTEND_DIR)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# -----------------------------
# Initialize Database
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Admin table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    cur.execute("SELECT * FROM admin WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO admin VALUES (?,?)", ("admin", "admin123"))

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            regno TEXT PRIMARY KEY,
            name TEXT,
            teamname TEXT,
            teamno TEXT,
            email TEXT
        )
    """)

    # Scores table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            teamno TEXT,
            teamname TEXT,
            score INTEGER
        )
    """)

    # Certificates table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            regno TEXT PRIMARY KEY,
            filename TEXT
        )
    """)

    conn.commit()
    conn.close()

# -----------------------------
# Login
# -----------------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")  # regno
        password = request.form.get("password")  # teamno

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Admin login
        cur.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        if cur.fetchone():
            conn.close()
            return redirect("/admin_dashboard.html")

        # User login
        cur.execute("SELECT * FROM users WHERE regno=? AND teamno=?", (username, password))
        if cur.fetchone():
            conn.close()
            return redirect(f"/user_dashboard.html?regno={username}")

        conn.close()
        return """<script>alert('Invalid Register Number or Team Number');window.location.href='/';</script>"""

    return app.send_static_file("login.html")

# -----------------------------
# Dashboard Pages
# -----------------------------
@app.route("/admin_dashboard.html")
def admin_dashboard():
    return app.send_static_file("admin_dashboard.html")

@app.route("/user_dashboard.html")
def user_dashboard():
    return app.send_static_file("user_dashboard.html")

# -----------------------------
# Add User
# -----------------------------
@app.route("/add_user", methods=["POST"])
def add_user():
    regno = request.form.get("regno")
    name = request.form.get("name")
    teamname = request.form.get("teamname")
    teamno = request.form.get("teamno")
    email = request.form.get("email")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (regno,name,teamname,teamno,email) VALUES (?,?,?,?,?)",
            (regno, name, teamname, teamno, email)
        )
        conn.commit()
        msg = "User added successfully"
    except sqlite3.IntegrityError:
        msg = "Register Number already exists"
    conn.close()
    return msg

# -----------------------------
# Add Score
# -----------------------------
@app.route("/add_score", methods=["POST"])
def add_score():
    teamno = request.form.get("teamno")
    teamname = request.form.get("teamname")
    score = request.form.get("score")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO scores VALUES (?,?,?)", (teamno, teamname, score))
    conn.commit()
    conn.close()
    return "Score added successfully"

# -----------------------------
# Add Certificate
# -----------------------------
@app.route("/add_certificate", methods=["POST"])
def add_certificate():
    regno = request.form.get("regno")
    file = request.files.get("certificate")
    if not file:
        return "No file selected"

    filename = f"{regno}_{file.filename}"
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO certificates VALUES (?,?)", (regno, filename))
    conn.commit()
    conn.close()
    return "Certificate uploaded successfully"

# -----------------------------
# Get Profile
# -----------------------------
@app.route("/get_profile/<regno>")
def get_profile(regno):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE regno=?", (regno,))
    user = cur.fetchone()
    conn.close()
    if user:
        return jsonify({
            "regno": user[0],
            "name": user[1],
            "teamname": user[2],
            "teamno": user[3],
            "email": user[4]
        })
    return jsonify({"error": "User not found"})

# -----------------------------
# Get Scores
# -----------------------------
@app.route("/get_scores")
def get_scores():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM scores ORDER BY score DESC")
    scores = cur.fetchall()
    conn.close()
    return jsonify({"scores": scores})

# -----------------------------
# Download Certificate
# -----------------------------
@app.route("/download_certificate/<regno>")
def download_certificate(regno):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT filename FROM certificates WHERE regno=?", (regno,))
    row = cur.fetchone()
    conn.close()
    if row:
        return send_from_directory(UPLOAD_FOLDER, row[0], as_attachment=True)
    return "Certificate not found"

# -----------------------------
# Run App
# -----------------------------
import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
