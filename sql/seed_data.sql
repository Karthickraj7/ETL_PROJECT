-- Sample users
INSERT INTO users (first_name, last_name, email, phone, address_line1, city, state, pincode) VALUES
('John', 'Doe', 'john.doe@email.com', '1234567890', '123 Main St', 'Mumbai', 'Maharashtra', '400001'),
('Jane', 'Smith', 'jane.smith@email.com', '9876543210', '456 Park Ave', 'Delhi', 'Delhi', '110001'),
('Bob', 'Johnson', 'bob.johnson@email.com', '5551234567', '789 Oak St', 'Bangalore', 'Karnataka', '560001');

-- Sample employment data
INSERT INTO employment_info (user_id, company_name, designation, start_date, end_date, is_current) VALUES
(1, 'Tech Corp', 'Software Engineer', '2022-01-15', NULL, true),
(2, 'Finance Ltd', 'Analyst', '2021-03-20', NULL, true),
(3, 'Retail Co', 'Manager', '2020-06-10', '2023-12-31', false);

-- Sample bank data
INSERT INTO user_bank_info (user_id, bank_name, account_number, ifsc, account_type) VALUES
(1, 'HDFC', '12345678901', 'HDFC0000123', 'Savings'),
(2, 'ICICI', '98765432109', 'ICIC0000567', 'Current'),
(3, 'HDFC', '55555555555', 'HDFC0000890', 'Savings');