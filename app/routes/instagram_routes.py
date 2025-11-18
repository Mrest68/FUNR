import flask
from flask import Blueprint, request, jsonify
from datetime import datetime

from sympy import re

instagram_bp = Blueprint('instagram', __name__)

def extract_instagram_url(text):
        pattern = r"(https?://(?:www\.)?instagram\.com/[^\s]+)"
        match = re.search(pattern, text)
        return match.group(0) if match else None

@instagram_bp.route('/save-instagram-data', methods=['POST'])
def save_instagram_data():
    data = request.form
    message = data.get('Body')
    instagram_reel = extract_instagram_url(message)
    # Here you would typically save the data to a database
    
    print("Received Instagram data:", data)
    print("Extracted Instagram URL:", instagram_reel)

    return jsonify({
        "status": "success",
        "message": "Instagram data saved successfully!",
        "instagram_url": instagram_reel
    }), 200
