from flask import Blueprint, request, jsonify
import sqlite3

notifications_bp = Blueprint("notifications", __name__)

DATABASE = "src/database/app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@notifications_bp.route("/unread", methods=["GET"])
def get_unread_notifications():
    user_id = request.args.get("user_id") # In a real app, get from auth token

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC", (user_id,))
    notifications = cursor.fetchall()
    conn.close()

    return jsonify([dict(n) for n in notifications])

@notifications_bp.route("/mark_read", methods=["POST"])
def mark_notification_read():
    data = request.get_json()
    notification_id = data.get("notification_id")

    if not notification_id:
        return jsonify({"error": "Notification ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE notification_id = ?", (notification_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Notification marked as read"})


