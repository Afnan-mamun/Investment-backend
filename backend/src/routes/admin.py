from flask import Blueprint, request, jsonify
import sqlite3

admin_bp = Blueprint("admin", __name__)

DATABASE = "src/database/app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Helper function for admin authentication (placeholder)
def admin_required(f):
    # In a real application, this would involve checking admin session or token
    # For now, it's a simple placeholder
    return f

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(amount_usd) FROM deposits WHERE status = \'Approved\'")
    total_deposits = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount_usd) FROM withdrawals WHERE status = \'Paid\'")
    total_withdrawals = cursor.fetchone()[0] or 0

    # Placeholder for active funds and top investors
    active_funds = 0
    top_investors = []

    conn.close()
    return jsonify({
        "total_users": total_users,
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "active_funds": active_funds,
        "top_investors": top_investors
    })

@admin_bp.route("/users", methods=["GET"])
@admin_required
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    search_by = request.args.get("search_by")
    query = request.args.get("query")

    if search_by and query:
        if search_by == "id":
            cursor.execute("SELECT * FROM users WHERE user_id LIKE ?", (f"%{query}%",))
        elif search_by == "email":
            cursor.execute("SELECT * FROM users WHERE email LIKE ?", (f"%{query}%",))
        elif search_by == "referral":
            cursor.execute("SELECT u.* FROM users u JOIN referrals r ON u.user_id = r.referred_user_id WHERE r.referrer_user_id LIKE ?", (f"%{query}%",))
        else:
            return jsonify({"error": "Invalid search_by parameter"}), 400
    else:
        cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@admin_bp.route("/user/<user_id>", methods=["GET"])
@admin_required
def get_user_details(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify(dict(user))
    return jsonify({"error": "User not found"}), 404

@admin_bp.route("/user/<user_id>/balance", methods=["PUT"])
@admin_required
def update_user_balance(user_id):
    data = request.get_json()
    amount = data.get("amount")
    operation = data.get("operation") # "add" or "subtract"

    if not amount or not operation:
        return jsonify({"error": "Amount and operation are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    if operation == "add":
        cursor.execute("UPDATE users SET balance_usd = balance_usd + ? WHERE user_id = ?", (amount, user_id))
    elif operation == "subtract":
        cursor.execute("UPDATE users SET balance_usd = balance_usd - ? WHERE user_id = ?", (amount, user_id))
    else:
        conn.close()
        return jsonify({"error": "Invalid operation"}), 400

    conn.commit()
    conn.close()
    return jsonify({"message": "User balance updated"})

@admin_bp.route("/user/<user_id>/status", methods=["PUT"])
@admin_required
def update_user_status(user_id):
    data = request.get_json()
    status = data.get("status") # "Active" or "Frozen"

    if not status or status not in ["Active", "Frozen"]:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET account_status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "User account status updated"})

@admin_bp.route("/user/<user_id>/level", methods=["PUT"])
@admin_required
def update_user_level(user_id):
    data = request.get_json()
    level = data.get("level")

    if not level:
        return jsonify({"error": "Level is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET level = ? WHERE user_id = ?", (level, user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "User level updated"})

@admin_bp.route("/deposits/pending", methods=["GET"])
@admin_required
def get_pending_deposits():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deposits WHERE status = \'Pending\'")
    deposits = cursor.fetchall()
    conn.close()
    return jsonify([dict(d) for d in deposits])

@admin_bp.route("/deposit/<deposit_id>/approve", methods=["POST"])
@admin_required
def approve_deposit(deposit_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, amount_usd FROM deposits WHERE deposit_id = ?", (deposit_id,))
    deposit = cursor.fetchone()
    if not deposit:
        conn.close()
        return jsonify({"error": "Deposit not found"}), 404

    cursor.execute("UPDATE deposits SET status = \'Approved\', approval_date = CURRENT_TIMESTAMP WHERE deposit_id = ?", (deposit_id,))
    cursor.execute("UPDATE users SET balance_usd = balance_usd + ? WHERE user_id = ?", (deposit["amount_usd"], deposit["user_id"]))
    conn.commit()
    conn.close()
    return jsonify({"message": "Deposit approved and user balance updated"})

@admin_bp.route("/deposit/<deposit_id>/reject", methods=["POST"])
@admin_required
def reject_deposit(deposit_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE deposits SET status = \'Rejected\' WHERE deposit_id = ?", (deposit_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Deposit rejected"})

@admin_bp.route("/withdrawals/pending", methods=["GET"])
@admin_required
def get_pending_withdrawals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM withdrawals WHERE status = \'Pending\'")
    withdrawals = cursor.fetchall()
    conn.close()
    return jsonify([dict(w) for w in withdrawals])

@admin_bp.route("/withdrawal/<withdrawal_id>/approve", methods=["POST"])
@admin_required
def approve_withdrawal(withdrawal_id):
    data = request.get_json()
    transaction_hash = data.get("transaction_hash")
    notes = data.get("notes")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE withdrawals SET status = \'Paid\', transaction_hash = ?, admin_notes = ?, process_date = CURRENT_TIMESTAMP WHERE withdrawal_id = ?", (transaction_hash, notes, withdrawal_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Withdrawal approved and marked as paid"})

@admin_bp.route("/withdrawal/<withdrawal_id>/reject", methods=["POST"])
@admin_required
def reject_withdrawal(withdrawal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE withdrawals SET status = \'Rejected\' WHERE withdrawal_id = ?", (withdrawal_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Withdrawal rejected"})

@admin_bp.route("/notifications/send", methods=["POST"])
@admin_required
def send_notification():
    data = request.get_json()
    message = data.get("message")
    user_id = data.get("user_id") # Optional, if None, send to all

    if not message:
        return jsonify({"error": "Message is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("INSERT INTO notifications (user_id, message) VALUES (?, ?)", (user_id, message))
    else:
        # Send to all users
        cursor.execute("INSERT INTO notifications (message) VALUES (?)", (message,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Notification sent"})

@admin_bp.route("/packages", methods=["POST"])
@admin_required
def create_package():
    data = request.get_json()
    package_name = data.get("package_name")
    roi_percentage = data.get("roi_percentage")
    duration_days = data.get("duration_days")
    min_investment_usd = data.get("min_investment_usd")
    max_investment_usd = data.get("max_investment_usd")

    if not all([package_name, roi_percentage, duration_days, min_investment_usd, max_investment_usd]):
        return jsonify({"error": "All package fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO investment_packages (package_name, roi_percentage, duration_days, min_investment_usd, max_investment_usd) VALUES (?, ?, ?, ?, ?)",
        (package_name, roi_percentage, duration_days, min_investment_usd, max_investment_usd),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Package created successfully"}), 201

@admin_bp.route("/packages/<package_id>", methods=["PUT"])
@admin_required
def edit_package(package_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if "package_name" in data: updates.append("package_name = ?"); params.append(data["package_name"])
    if "roi_percentage" in data: updates.append("roi_percentage = ?"); params.append(data["roi_percentage"])
    if "duration_days" in data: updates.append("duration_days = ?"); params.append(data["duration_days"])
    if "min_investment_usd" in data: updates.append("min_investment_usd = ?"); params.append(data["min_investment_usd"])
    if "max_investment_usd" in data: updates.append("max_investment_usd = ?"); params.append(data["max_investment_usd"])

    if not updates:
        conn.close()
        return jsonify({"error": "No fields to update"}), 400

    query = f"UPDATE investment_packages SET {', '.join(updates)} WHERE package_id = ?"
    params.append(package_id)
    
    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()
    return jsonify({"message": "Package updated successfully"})

@admin_bp.route("/packages/<package_id>", methods=["DELETE"])
@admin_required
def delete_package(package_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM investment_packages WHERE package_id = ?", (package_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Package deleted successfully"})

@admin_bp.route("/system/maintenance", methods=["PUT"])
@admin_required
def toggle_maintenance_mode():
    data = request.get_json()
    status = data.get("status") # "on" or "off"

    if status not in ["on", "off"]:
        return jsonify({"error": "Invalid status, must be \'on\' or \'off\'"}), 400

    # In a real app, this would update a config file or database setting
    # For now, just return a success message
    return jsonify({"message": f"Maintenance mode turned {status}"})

@admin_bp.route("/activity_log", methods=["GET"])
@admin_required
def get_activity_log():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin_activity_log ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()
    return jsonify([dict(l) for l in logs])

@admin_bp.route("/batch/deposits/approve", methods=["POST"])
@admin_required
def batch_approve_deposits():
    data = request.get_json()
    deposit_ids = data.get("deposit_ids")

    if not deposit_ids or not isinstance(deposit_ids, list):
        return jsonify({"error": "deposit_ids (list) is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    for deposit_id in deposit_ids:
        cursor.execute("SELECT user_id, amount_usd FROM deposits WHERE deposit_id = ?", (deposit_id,))
        deposit = cursor.fetchone()
        if deposit:
            cursor.execute("UPDATE deposits SET status = \'Approved\', approval_date = CURRENT_TIMESTAMP WHERE deposit_id = ?", (deposit_id,))
            cursor.execute("UPDATE users SET balance_usd = balance_usd + ? WHERE user_id = ?", (deposit["amount_usd"], deposit["user_id"]))
    conn.commit()
    conn.close()
    return jsonify({"message": f"{len(deposit_ids)} deposits approved"})

@admin_bp.route("/batch/withdrawals/approve", methods=["POST"])
@admin_required
def batch_approve_withdrawals():
    data = request.get_json()
    withdrawal_ids = data.get("withdrawal_ids")
    transaction_hash = data.get("transaction_hash", "")
    notes = data.get("notes", "")

    if not withdrawal_ids or not isinstance(withdrawal_ids, list):
        return jsonify({"error": "withdrawal_ids (list) is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    for withdrawal_id in withdrawal_ids:
        cursor.execute("UPDATE withdrawals SET status = \'Paid\', transaction_hash = ?, admin_notes = ?, process_date = CURRENT_TIMESTAMP WHERE withdrawal_id = ?", (transaction_hash, notes, withdrawal_id))
    conn.commit()
    conn.close()
    return jsonify({"message": f"{len(withdrawal_ids)} withdrawals approved"})

@admin_bp.route("/batch/users/level", methods=["POST"])
@admin_required
def batch_update_user_levels():
    data = request.get_json()
    user_ids = data.get("user_ids")
    level = data.get("level")

    if not user_ids or not isinstance(user_ids, list) or not level:
        return jsonify({"error": "user_ids (list) and level are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    for user_id in user_ids:
        cursor.execute("UPDATE users SET level = ? WHERE user_id = ?", (level, user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Levels updated for {len(user_ids)} users"})

@admin_bp.route("/multilang/texts", methods=["GET"])
@admin_required
def get_multilang_texts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM multi_language_text")
    texts = cursor.fetchall()
    conn.close()
    return jsonify([dict(t) for t in texts])

@admin_bp.route("/multilang/text/<text_key>", methods=["PUT"])
@admin_required
def update_multilang_text(text_key):
    data = request.get_json()
    lang_ru = data.get("lang_ru")
    lang_en = data.get("lang_en")
    lang_bd = data.get("lang_bd")

    if not any([lang_ru, lang_en, lang_bd]):
        return jsonify({"error": "At least one language text is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if lang_ru is not None: updates.append("lang_ru = ?"); params.append(lang_ru)
    if lang_en is not None: updates.append("lang_en = ?"); params.append(lang_en)
    if lang_bd is not None: updates.append("lang_bd = ?"); params.append(lang_bd)

    query = f"UPDATE multi_language_text SET {', '.join(updates)} WHERE text_key = ?"
    params.append(text_key)

    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()
    return jsonify({"message": "Multi-language text updated"})


