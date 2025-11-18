import flask
from flask import Blueprint, request, jsonify

restaurant_bp = Blueprint('restaurant', __name__)


@restaurant_bp.route('/save-restaurants', methods=['POST'])
def save_restaurants():
    data = request.get_json()
    # Here you would typically save the data to a database
    print("Received restaurant data:", data)
    return jsonify({"status": "success", "message": "Restaurants saved successfully!"}), 200


