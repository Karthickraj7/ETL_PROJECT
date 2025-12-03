
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address_line1 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(20),
    created_at TIMESTAMP DEFAULT now()
);

--Employment info table
CREATE TABLE employment_info (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255),
    designation VARCHAR(100),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN
);

-- Bank info table
CREATE TABLE user_bank_info (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    bank_name VARCHAR(255),
    account_number VARCHAR(50),
    ifsc VARCHAR(20),
    account_type VARCHAR(50)
);