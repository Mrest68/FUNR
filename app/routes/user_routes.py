import flask
from flask import Blueprint, request, jsonify


user_bp = Blueprint('user', __name__)

@user_bp.route('/save-users', methods=['POST'])
def save_users():
    data = request.get_json()
    # Here you would typically save the data to a database
    print("Received user data:", data)
    return jsonify({"status": "success", "message": "Users saved successfully!"}), 200

