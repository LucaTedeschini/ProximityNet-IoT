import secrets
from flask import Flask, jsonify, request, g
from werkzeug.security import generate_password_hash, check_password_hash

from utilities.manage_db import init_db, get_db_connection, close_connection
from utilities.authentication import validate_username, token_required

app = Flask(__name__)

@app.teardown_appcontext
def teardown_db(exception):
    close_connection(exception)

@app.route("/api/user/register", methods=['POST'])
def api_user_register():
    data = request.get_json()
    if not data: return jsonify({"status": 1, "message": "Invalid JSON"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not validate_username(username): return jsonify({"status": 1, "message": "Invalid username format"}), 400
    if len(password) < 6: return jsonify({"status": 1, "message": "Password too short"}), 400

    hashed_pw = generate_password_hash(password)
    
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO credentials (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        return jsonify({"status": 0, "message": "Username correctly registered"}), 201
    except conn.IntegrityError:
        return jsonify({"status": 1, "message": f"Username '{username}' already exists"}), 409
    except Exception as e:
        return jsonify({"status": 2, "message": f"Error while registering username: {e}"}), 500

@app.route("/api/user/login", methods=['POST'])
def api_user_login():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"status": 1, "message": "Username and password required"}), 400

    username = data["username"]
    password = data["password"]

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM credentials WHERE username = ?", (username,)).fetchone()

    if user is None:
        return jsonify({"status": 1, "message": "User does not exists"}), 401
    
    if user is None or not check_password_hash(user['password'], password):
        return jsonify({"status": 2, "message": "Invalid credentials"}), 401

    token = secrets.token_hex(32)
    user_id = user['id']

    try:
        conn.execute(
            """
            INSERT INTO auth_tokens (user_id, token) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET token = excluded.token, created_at = CURRENT_TIMESTAMP
            """,
            (user_id, token)
        )
        conn.commit()
        return jsonify({"status": 0, "message": "Login successful", "data": {"token": token}})
    except Exception as e:
        return jsonify({"status": 3, "message": f"Could not issue token: {e}"}), 500

@app.route("/api/get_my_info", methods=['GET'])
@token_required
def get_my_info():
    user = g.current_user
    return jsonify({
        "status": 0,
        "data": {
            "id": user['id'],
            "username": user['username'],
        }
    })

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=9009)