from flask import Blueprint, request, jsonify
import sqlite3

deposits_bp = Blueprint("deposits", __name__)

DATABASE = "src/database/app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@deposits_bp.route("/request", methods=["POST"])
def request_deposit():
    data = request.get_json()
    user_id = data.get("user_id") # In a real app, get from auth token
    amount_usd = data.get("amount_usd")
    txid = data.get("txid")
    screenshot_url = data.get("screenshot_url")

    if not user_id or not amount_usd:
        return jsonify({"error": "User ID and amount are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO deposits (user_id, amount_usd, txid, screenshot_url, status) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount_usd, txid, screenshot_url, "Pending"),
    )
    conn.commit()
    deposit_id = cursor.lastrowid
    conn.close()

    return jsonify({"message": "Deposit request submitted", "deposit_id": deposit_id}), 201

@deposits_bp.route("/history", methods=["GET"])
def get_deposit_history():
    user_id = request.args.get("user_id") # In a real app, get from auth token

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deposits WHERE user_id = ? ORDER BY request_date DESC", (user_id,))
    deposits = cursor.fetchall()
    conn.close()

    return jsonify([dict(d) for d in deposits])


