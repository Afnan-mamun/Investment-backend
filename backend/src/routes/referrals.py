from flask import Blueprint, request, jsonify
import sqlite3

referrals_bp = Blueprint("referrals", __name__)

DATABASE = "src/database/app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@referrals_bp.route("/info", methods=["GET"])
def get_referral_info():
    user_id = request.args.get("user_id") # In a real app, get from auth token

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT referral_link FROM users WHERE user_id = ?", (user_id,))
    referral_link = cursor.fetchone()["referral_link"]

    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_user_id = ?", (user_id,))
    referred_users_count = cursor.fetchone()[0]

    # This part would be more complex in a real app, involving a ledger for bonuses
    # For now, a placeholder for credited bonus amount
    credited_bonus_amount = 0.0

    conn.close()

    return jsonify({
        "referral_link": referral_link,
        "referred_users_count": referred_users_count,
        "credited_bonus_amount": credited_bonus_amount
    })


