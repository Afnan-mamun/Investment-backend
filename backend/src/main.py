from flask import Flask, jsonify, send_from_directory
import sqlite3
import os

# Import blueprints
from src.routes.auth import auth_bp
from src.routes.deposits import deposits_bp
from src.routes.withdrawals import withdrawals_bp
from src.routes.investments import investments_bp
from src.routes.referrals import referrals_bp
from src.routes.notifications import notifications_bp
from src.routes.admin import admin_bp

app = Flask(__name__, static_folder='static', static_url_path='/')

DATABASE = os.path.join(app.root_path, 'database', 'app.db')

def init_db():
    with app.app_context():
        conn = sqlite3.connect(DATABASE)
        with app.open_resource('database/schema.sql', mode='r') as f:
            conn.cursor().executescript(f.read())
        conn.commit()
        conn.close()

# Initialize database if it doesn't exist
if not os.path.exists(DATABASE):
    init_db()

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(deposits_bp, url_prefix='/api/deposit')
app.register_blueprint(withdrawals_bp, url_prefix='/api/withdrawal')
app.register_blueprint(investments_bp, url_prefix='/api/investments')
app.register_blueprint(referrals_bp, url_prefix='/api/referral')
app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


