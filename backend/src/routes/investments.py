from flask import Blueprint, request, jsonify
import sqlite3
from datetime import datetime, timedelta

investments_bp = Blueprint("investments", __name__)

DATABASE = "src/database/app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@investments_bp.route("/packages", methods=["GET"])
def get_packages():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investment_packages")
    packages = cursor.fetchall()
    conn.close()
    return jsonify([dict(p) for p in packages])

@investments_bp.route("/invest", methods=["POST"])
def invest():
    data = request.get_json()
    user_id = data.get("user_id") # In a real app, get from auth token
    package_id = data.get("package_id")
    amount_usd = data.get("amount_usd")

    if not user_id or not package_id or not amount_usd:
        return jsonify({"error": "User ID, package ID, and amount are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check user balance
    cursor.execute("SELECT balance_usd FROM users WHERE user_id = ?", (user_id,))
    user_balance = cursor.fetchone()["balance_usd"]
    if user_balance < amount_usd:
        conn.close()
        return jsonify({"error": "Insufficient balance"}), 400

    # Get package details
    cursor.execute("SELECT * FROM investment_packages WHERE package_id = ?", (package_id,))
    package = cursor.fetchone()
    if not package:
        conn.close()
        return jsonify({"error": "Investment package not found"}), 404

    if not (package["min_investment_usd"] <= amount_usd <= package["max_investment_usd"]):
        conn.close()
        return jsonify({"error": f"Investment amount must be between {package["min_investment_usd"]} and {package["max_investment_usd"]}"}), 400

    # Deduct amount from user balance
    cursor.execute("UPDATE users SET balance_usd = balance_usd - ? WHERE user_id = ?", (amount_usd, user_id))

    # Calculate expected profit and end date
    expected_profit_usd = amount_usd * (1 + package["roi_percentage"] / 100)
    start_date = datetime.now()
    end_date = start_date + timedelta(days=package["duration_days"])

    # Record investment
    cursor.execute(
        "INSERT INTO investments (user_id, package_id, invested_amount_usd, start_date, end_date, expected_profit_usd, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, package_id, amount_usd, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S"), expected_profit_usd, "Active"),
    )
    conn.commit()
    investment_id = cursor.lastrowid
    conn.close()

    return jsonify({"message": "Investment successful", "investment_id": investment_id}), 201

@investments_bp.route("/active", methods=["GET"])
def get_active_investments():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investments WHERE user_id = ? AND status = ? ORDER BY start_date DESC", (user_id, "Active"))
    investments = cursor.fetchall()
    conn.close()
    return jsonify([dict(i) for i in investments])

@investments_bp.route("/history", methods=["GET"])
def get_investment_history():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investments WHERE user_id = ? ORDER BY start_date DESC", (user_id,))
    investments = cursor.fetchall()
    conn.close()
    return jsonify([dict(i) for i in investments])


