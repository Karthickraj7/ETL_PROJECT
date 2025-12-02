from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from config import config

app = Flask(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


def get_db_connection():
    return psycopg2.connect(config.DATABASE_URL)


# POST USER
@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO users (first_name, last_name, email, phone, address_line1, city, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (data['first_name'], data['last_name'], data['email'], data['phone'],
              data['address_line1'], data['city'], data['state'], data['pincode']))
        user_id = cur.fetchone()[0]

        if 'employment' in data:
            e = data['employment']
            cur.execute("""
                INSERT INTO employment_info (user_id, company_name, designation, start_date, end_date, is_current)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, e['company_name'], e['designation'], e['start_date'],
                  e.get('end_date'), e.get('is_current', True)))

        if 'bank' in data:
            b = data['bank']
            cur.execute("""
                INSERT INTO user_bank_info (user_id, bank_name, account_number, ifsc, account_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, b['bank_name'], b['account_number'], b['ifsc'], b['account_type']))

        conn.commit()

        cur2 = conn.cursor(cursor_factory=RealDictCursor)
        cur2.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur2.fetchone()
        cur2.close()

        return jsonify({
            "created_user_id": user_id,
            "created_user": user
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        conn.close()


# GET ALL USERS
@app.route('/users', methods=['GET'])
def get_users():
    company = request.args.get('company')
    bank = request.args.get('bank')
    pincode = request.args.get('pincode')

    query = """
        SELECT u.*, 
               e.company_name AS company_name, 
               e.designation AS designation,
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

    return jsonify({"users": users}), 200


# GET SINGLE USER (Clean Output)
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        cur.execute("SELECT * FROM employment_info WHERE user_id = %s AND is_current = true", (user_id,))
        employment = cur.fetchone()

        cur.execute("SELECT * FROM user_bank_info WHERE user_id = %s", (user_id,))
        bank = cur.fetchone()

        user["employment"] = employment
        user["bank"] = bank

        return jsonify(user), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        conn.close()




# PUT — CLEAN JSON RESPONSE



@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    updated_sections = []
    updated_user_fields = []
    updated_employment_fields = []
    updated_bank_fields = []

    try:
        # Fetch old user data
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        old_user = cur.fetchone()
        if not old_user:
            return jsonify({"error": "User not found"}), 404

        # ---------------- USER UPDATE ----------------
        user_fields = ["first_name", "last_name", "email", "phone",
                       "address_line1", "city", "state", "pincode"]

        for field in user_fields:
            if field in data and data[field] != old_user[field]:
                updated_user_fields.append(field)

        if updated_user_fields:
            updated_sections.append("user")
            cur.execute("""
                UPDATE users SET 
                    first_name=COALESCE(%s, first_name),
                    last_name=COALESCE(%s, last_name),
                    email=COALESCE(%s, email),
                    phone=COALESCE(%s, phone),
                    address_line1=COALESCE(%s, address_line1),
                    city=COALESCE(%s, city),
                    state=COALESCE(%s, state),
                    pincode=COALESCE(%s, pincode)
                WHERE id=%s
            """, (
                data.get("first_name"),
                data.get("last_name"),
                data.get("email"),
                data.get("phone"),
                data.get("address_line1"),
                data.get("city"),
                data.get("state"),
                data.get("pincode"),
                user_id
            ))

        # ---------------- EMPLOYMENT UPDATE ----------------
        if "employment" in data:
            new_emp = data["employment"]

            cur.execute("SELECT * FROM employment_info WHERE user_id=%s", (user_id,))
            old_emp = cur.fetchone()

            if old_emp:
                for key in ["company_name", "designation", "start_date", "end_date", "is_current"]:
                    if key in new_emp and new_emp[key] != old_emp[key]:
                        updated_employment_fields.append(key)

                if updated_employment_fields:
                    updated_sections.append("employment")

                cur.execute("""
                    UPDATE employment_info SET
                        company_name=COALESCE(%s, company_name),
                        designation=COALESCE(%s, designation),
                        start_date=COALESCE(%s, start_date),
                        end_date=%s,
                        is_current=COALESCE(%s, is_current)
                    WHERE user_id=%s
                """, (
                    new_emp.get("company_name"),
                    new_emp.get("designation"),
                    new_emp.get("start_date"),
                    new_emp.get("end_date"),
                    new_emp.get("is_current"),
                    user_id
                ))

            else:
                updated_sections.append("employment")
                updated_employment_fields = list(new_emp.keys())

                cur.execute("""
                    INSERT INTO employment_info 
                        (user_id, company_name, designation, start_date, end_date, is_current)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    new_emp.get("company_name"),
                    new_emp.get("designation"),
                    new_emp.get("start_date"),
                    new_emp.get("end_date"),
                    new_emp.get("is_current", True)
                ))

        # ---------------- BANK UPDATE ----------------
        if "bank" in data:
            new_bank = data["bank"]

            cur.execute("SELECT * FROM user_bank_info WHERE user_id=%s", (user_id,))
            old_bank = cur.fetchone()

            if old_bank:
                for key in ["bank_name", "account_number", "ifsc", "account_type"]:
                    if key in new_bank and new_bank[key] != old_bank[key]:
                        updated_bank_fields.append(key)

                if updated_bank_fields:
                    updated_sections.append("bank")

                cur.execute("""
                    UPDATE user_bank_info SET
                        bank_name=COALESCE(%s, bank_name),
                        account_number=COALESCE(%s, account_number),
                        ifsc=COALESCE(%s, ifsc),
                        account_type=COALESCE(%s, account_type)
                    WHERE user_id=%s
                """, (
                    new_bank.get("bank_name"),
                    new_bank.get("account_number"),
                    new_bank.get("ifsc"),
                    new_bank.get("account_type"),
                    user_id
                ))

            else:
                updated_sections.append("bank")
                updated_bank_fields = list(new_bank.keys())

                cur.execute("""
                    INSERT INTO user_bank_info 
                        (user_id, bank_name, account_number, ifsc, account_type)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    user_id,
                    new_bank.get("bank_name"),
                    new_bank.get("account_number"),
                    new_bank.get("ifsc"),
                    new_bank.get("account_type")
                ))

        conn.commit()

        # ---------------- FINAL RESPONSE ONLY CHANGES ----------------
        return jsonify({
            "updated_user_id": user_id,
            "updated_sections": updated_sections,
            "updated_user_fields": updated_user_fields,
            "updated_employment_fields": updated_employment_fields,
            "updated_bank_fields": updated_bank_fields
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        conn.close()










# DELETE USER
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()

        return jsonify({"deleted_user_id": user_id}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
