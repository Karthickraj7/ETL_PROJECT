from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from config import config
from flask import Response
import csv
import io

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(config.DATABASE_URL)

# POST /users - Create user with employment and bank details
@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Insert user
        cur.execute("""
            INSERT INTO users (first_name, last_name, email, phone, address_line1, city, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (data['first_name'], data['last_name'], data['email'], data['phone'], 
              data['address_line1'], data['city'], data['state'], data['pincode']))
        
        user_id = cur.fetchone()[0]
        
        # Insert employment info if provided
        if 'employment' in data:
            employment = data['employment']
            cur.execute("""
                INSERT INTO employment_info (user_id, company_name, designation, start_date, end_date, is_current)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, employment['company_name'], employment['designation'], 
                  employment['start_date'], employment.get('end_date'), employment.get('is_current', True)))
        
        # Insert bank info if provided
        if 'bank' in data:
            bank = data['bank']
            cur.execute("""
                INSERT INTO user_bank_info (user_id, bank_name, account_number, ifsc, account_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, bank['bank_name'], bank['account_number'], bank['ifsc'], bank['account_type']))
        
        conn.commit()
        return jsonify({"message": "User created successfully", "user_id": user_id}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()















# GET /users - Get all users with filters
@app.route('/users/csv', methods=['GET'])
def get_users_csv():
    company = request.args.get('company')
    bank = request.args.get('bank')
    pincode = request.args.get('pincode')

    query = """
        SELECT u.*, 
               e.company_name, e.designation,
               b.bank_name, b.account_number
        FROM users u
        LEFT JOIN employment_info e ON u.id = e.user_id AND e.is_current = true
        LEFT JOIN user_bank_info b ON u.id = b.user_id
        WHERE 1=1
    """
    params = []

    if company:
        query += " AND e.company_name = %s"
        params.append(company)
    if bank:
        query += " AND b.bank_name = %s"
        params.append(bank)
    if pincode:
        query += " AND u.pincode = %s"
        params.append(pincode)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, params)
    users = cur.fetchall()
    cur.close()
    conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=users[0].keys())
    writer.writeheader()
    writer.writerows(users)

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "inline; filename=users.csv"}
    )












# GET /users/{id} - Get specific user
@app.route('/users/<int:user_id>/csv', methods=['GET'])
def get_user_csv(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=user.keys())
    writer.writeheader()
    writer.writerow(user)

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=user_{user_id}.csv"}
    )















# PUT /users/{id} - Update user
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Update user basic info
        cur.execute("""
            UPDATE users SET first_name=%s, last_name=%s, email=%s, phone=%s, 
            address_line1=%s, city=%s, state=%s, pincode=%s WHERE id=%s
        """, (data['first_name'], data['last_name'], data['email'], data['phone'],
              data['address_line1'], data['city'], data['state'], data['pincode'], user_id))
        
        conn.commit()
        return jsonify({"message": "User updated successfully"})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()

# DELETE /users/{id} - Delete user
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return jsonify({"message": "User deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()

# POST /users/{id}/employment - Add employment record
@app.route('/users/<int:user_id>/employment', methods=['POST'])
def add_employment(user_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO employment_info (user_id, company_name, designation, start_date, end_date, is_current)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, data['company_name'], data['designation'], 
              data['start_date'], data.get('end_date'), data.get('is_current', True)))
        
        conn.commit()
        return jsonify({"message": "Employment record added successfully"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()

# POST /users/{id}/bank - Add bank record
@app.route('/users/<int:user_id>/bank', methods=['POST'])
def add_bank(user_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO user_bank_info (user_id, bank_name, account_number, ifsc, account_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, data['bank_name'], data['account_number'], data['ifsc'], data['account_type']))
        
        conn.commit()
        return jsonify({"message": "Bank record added successfully"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)