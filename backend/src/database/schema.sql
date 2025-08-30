-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(20) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    balance_usd DECIMAL(10, 2) DEFAULT 0.00,
    level VARCHAR(50) DEFAULT 'Bronze',
    account_status VARCHAR(50) DEFAULT 'Active',
    referral_link VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ledger Table
CREATE TABLE IF NOT EXISTS ledger (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount_usd DECIMAL(10, 2) NOT NULL,
    description TEXT,
    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Deposits Table
CREATE TABLE IF NOT EXISTS deposits (
    deposit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(20) NOT NULL,
    amount_usd DECIMAL(10, 2) NOT NULL,
    txid VARCHAR(255),
    screenshot_url VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Pending',
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approval_date TIMESTAMP,
    admin_notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Withdrawals Table
CREATE TABLE IF NOT EXISTS withdrawals (
    withdrawal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(20) NOT NULL,
    amount_usd DECIMAL(10, 2) NOT NULL,
    withdrawal_address VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    transaction_hash VARCHAR(255),
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    process_date TIMESTAMP,
    admin_notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- InvestmentPackages Table
CREATE TABLE IF NOT EXISTS investment_packages (
    package_id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_name VARCHAR(255) UNIQUE NOT NULL,
    roi_percentage DECIMAL(5, 2) NOT NULL,
    duration_days INTEGER NOT NULL,
    min_investment_usd DECIMAL(10, 2) NOT NULL,
    max_investment_usd DECIMAL(10, 2) NOT NULL
);

-- Investments Table
CREATE TABLE IF NOT EXISTS investments (
    investment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(20) NOT NULL,
    package_id INTEGER NOT NULL,
    invested_amount_usd DECIMAL(10, 2) NOT NULL,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    expected_profit_usd DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'Active',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (package_id) REFERENCES investment_packages(package_id)
);

-- Referrals Table
CREATE TABLE IF NOT EXISTS referrals (
    referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_user_id VARCHAR(20) NOT NULL,
    referred_user_id VARCHAR(20) UNIQUE NOT NULL,
    signup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    first_deposit_approved BOOLEAN DEFAULT FALSE,
    referral_bonus_credited BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (referrer_user_id) REFERENCES users(user_id),
    FOREIGN KEY (referred_user_id) REFERENCES users(user_id)
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(20),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- AdminActivityLog Table
CREATE TABLE IF NOT EXISTS admin_activity_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user_id VARCHAR(20) NOT NULL,
    action TEXT NOT NULL,
    target_entity VARCHAR(255),
    target_id VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    -- FOREIGN KEY (admin_user_id) REFERENCES admins(admin_id) -- Assuming an admins table
);

-- MultiLanguageText Table
CREATE TABLE IF NOT EXISTS multi_language_text (
    text_key VARCHAR(255) PRIMARY KEY,
    lang_ru TEXT NOT NULL,
    lang_en TEXT NOT NULL,
    lang_bd TEXT NOT NULL
);


