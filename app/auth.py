from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db
import jwt
import datetime
from .utils.token_required import token_required

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()  # Get JSON data from the frontend
    if data is None:
        print("No JSON data received")
        return {"error": "No data received"}, 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    print(data)

    # Check if any required fields are missing
    if not name or not email or not password:
        return jsonify({"error": "All fields (name, email, password) are required."}), 400

    # Check if user already exists
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"error": "Email already exists."}), 400

    # Validate input lengths
    if len(name) < 3:
        return jsonify({"error": "Name must be greater than 3 characters."}), 400
    if len(email) < 4:
        return jsonify({"error": "Email must be valid."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 7 characters."}), 400

    # Create new user
    new_user = User(name=name, email=email, password=generate_password_hash(password, method='pbkdf2:sha256')) # type: ignore
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": f"Account created successfully! Welcome, {name}"}), 200

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()  # Get JSON data from the frontend
    email = str(data.get('email'))
    password = str(data.get('password'))
    print(data)
    user = User.query.filter_by(email=email).first()

    if user:
        if check_password_hash(user.password, password):
            # Tạo JWT Token
            token = jwt.encode(
                {
                    "user_id": user.id,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)  
                },
                "secret_key",
                algorithm="HS256"
            )
            return jsonify({"message": "Logged in successfully", "token": token}), 200
        else:
            return jsonify({"error": "Incorrect password, try again!"}), 401
    else:
        return jsonify({"error": "Email does not exist"}), 404

@auth.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    return jsonify({"message": f"Hello, {current_user.name}!"}), 200
