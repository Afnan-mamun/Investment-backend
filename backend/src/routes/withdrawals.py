from flask import Blueprint, request, jsonify
import sqlite3

withdrawals_bp = Blueprint("withdrawals", __name__)

DATABASE = "src/database/app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@withdrawals_bp.route("/request", methods=["POST"])
def request_withdrawal():
    data = request.get_json()
    user_id = data.get("user_id") # In a real app, get from auth token
    amount_usd = data.get("amount_usd")
    withdrawal_address = data.get("withdrawal_address")

    if not user_id or not amount_usd or not withdrawal_address:
        return jsonify({"error": "User ID, amount, and withdrawal address are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user has sufficient balance
    cursor.execute("SELECT balance_usd FROM users WHERE user_id = ?", (user_id,))
    user_balance = cursor.fetchone()["balance_usd"]
    if user_balance < amount_usd:
        conn.close()
        return jsonify({"error": "Insufficient balance"}), 400

    cursor.execute(
        "INSERT INTO withdrawals (user_id, amount_usd, withdrawal_address, status) VALUES (?, ?, ?, ?)",
        (user_id, amount_usd, withdrawal_address, "Pending"),
    )
    conn.commit()
    withdrawal_id = cursor.lastrowid
    conn.close()

    return jsonify({"message": "Withdrawal request submitted", "withdrawal_id": withdrawal_id}), 201

@withdrawals_bp.route("/history", methods=["GET"])
def get_withdrawal_history():
    user_id = request.args.get("user_id") # In a real app, get from auth token

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM withdrawals WHERE user_id = ? ORDER BY request_date DESC", (user_id,))
    withdrawals = cursor.fetchall()
    conn.close()

    return jsonify([dict(w) for w in withdrawals])


