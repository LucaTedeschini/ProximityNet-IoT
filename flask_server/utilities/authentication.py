import re
import functools
from flask import request, jsonify, g
from .manage_db import get_db_connection 

def validate_username(username: str) -> bool:
    return bool(re.match(r"^[A-Za-z0-9_]{3,32}$", username))

def token_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split()[1]
            except IndexError:
                return jsonify({"status": 1, "message": "Malformed token format. Use 'Bearer <token>'"}), 401

        if not token:
            return jsonify({"status": 1, "message": "Token is missing!"}), 401

        conn = get_db_connection()
        user = conn.execute(
            "SELECT c.* FROM credentials c JOIN auth_tokens t ON c.id = t.user_id WHERE t.token = ?",
            (token,)
        ).fetchone()

        if user is None:
            return jsonify({"status": 1, "message": "Token is invalid or has been revoked!"}), 401
        
        g.current_user = user
        
        return f(*args, **kwargs)
    return decorated_function