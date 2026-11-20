import os
import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Random value created at startup for login sessions (no secret key stored in the code)
app.secret_key = os.urandom(24)
DB_NAME = "fittrack.db"

# MET values (Metabolic Equivalent of Task) for each activity
MET_VALUES = {"Walking": 3.5, "Running": 9.8, "Cycling": 7.5, "Swimming": 8.0, "Yoga": 2.5}


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            workout_date TEXT NOT NULL,
            activity TEXT NOT NULL,
            duration_min REAL NOT NULL,
            weight_kg REAL NOT NULL,
            calories REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("dashboard.html", email=session["email"])


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or len(password) < 6:
        return jsonify(error="Enter an email and a password of at least 6 characters"), 400
    try:
        with get_db() as db:
            db.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)",
                       (email, generate_password_hash(password)))
    except sqlite3.IntegrityError:
        return jsonify(error="Account already exists"), 409
    return jsonify(message="Account created"), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?",
                          (data.get("email", "").strip().lower(),)).fetchone()
    if user is None or not check_password_hash(user["password_hash"], data.get("password", "")):
        return jsonify(error="Invalid email or password"), 401
    session["user_id"], session["email"] = user["id"], user["email"]
    return jsonify(message="Logged in")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/api/workouts", methods=["GET"])
def list_workouts():
    if "user_id" not in session:
        return jsonify(error="Login required"), 401
    with get_db() as db:
        rows = db.execute("SELECT * FROM workouts WHERE user_id = ? ORDER BY workout_date",
                          (session["user_id"],)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/workouts", methods=["POST"])
def add_workout():
    if "user_id" not in session:
        return jsonify(error="Login required"), 401
    data = request.get_json()
    try:
        workout_date = data["workout_date"]
        activity = data["activity"]
        duration_min = float(data["duration_min"])
        weight_kg = float(data["weight_kg"])
        if activity not in MET_VALUES:
            raise ValueError("Unknown activity")
        if duration_min <= 0 or weight_kg <= 0:
            raise ValueError("Duration and weight must be greater than zero")
    except (KeyError, TypeError, ValueError) as e:
        return jsonify(error=f"Invalid input: {e}"), 400

    # Calories = MET x body weight (kg) x duration (hours)
    calories = round(MET_VALUES[activity] * weight_kg * (duration_min / 60), 1)

    with get_db() as db:
        db.execute("""INSERT INTO workouts
            (user_id, workout_date, activity, duration_min, weight_kg, calories)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (session["user_id"], workout_date, activity, duration_min, weight_kg, calories))
    return jsonify(message="Workout saved", calories=calories), 201


@app.route("/api/workouts/<int:workout_id>", methods=["DELETE"])
def delete_workout(workout_id):
    if "user_id" not in session:
        return jsonify(error="Login required"), 401
    with get_db() as db:
        db.execute("DELETE FROM workouts WHERE id = ? AND user_id = ?",
                   (workout_id, session["user_id"]))
    return jsonify(message="Workout deleted")


@app.route("/api/health")
def health():
    try:
        with get_db() as db:
            db.execute("SELECT 1")
        return jsonify(status="ok", database="connected")
    except sqlite3.Error:
        return jsonify(status="error", database="unavailable"), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
