from flask import Blueprint, request, jsonify
import sqlite3
from passlib.hash import pbkdf2_sha256
import uuid

auth_bp = Blueprint("auth", __name__)

DATABASE = "src/database/app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    referral_id = data.get("referral_id")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "User with this email already exists"}), 409

    # Hash the password
    hashed_password = pbkdf2_sha256.hash(password.encode("utf-8"))

    # Generate a unique user ID and referral link
    user_id = f"USR{str(uuid.uuid4().int)[:6]}"
    referral_link = f"/ref/{user_id}"

    # Insert new user into the database
    cursor.execute(
        "INSERT INTO users (user_id, email, password_hash, referral_link) VALUES (?, ?, ?, ?)",
        (user_id, email, hashed_password, referral_link),
    )
    conn.commit()

    # Handle referral if provided
    if referral_id:
        cursor.execute("SELECT user_id FROM users WHERE referral_link = ?", (referral_id,))
        referrer = cursor.fetchone()
        if referrer:
            cursor.execute(
                "INSERT INTO referrals (referrer_user_id, referred_user_id) VALUES (?, ?)",
                (referrer["user_id"], user_id),
            )
            conn.commit()

    conn.close()

    return jsonify({"message": "User created successfully", "user_id": user_id}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user or not pbkdf2_sha256.verify(password.encode("utf-8"), user["password_hash"]):
        conn.close()
        return jsonify({"error": "Invalid credentials"}), 401

    conn.close()

    # In a real application, you would generate and return a JWT token here
    return jsonify({"message": "Login successful", "user_id": user["user_id"]})


