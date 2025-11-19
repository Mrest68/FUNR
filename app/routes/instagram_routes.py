import flask
import re
from flask import Blueprint, request, jsonify
from datetime import datetime


instagram_bp = Blueprint('instagram', __name__)

def extract_instagram_url(text):
        pattern = r"(https?://(?:www\.)?instagram\.com/[^\s]+)"
        match = re.search(pattern, text)
        return match.group(0) if match else None

@instagram_bp.route('/save-instagram-data', methods=['POST'])
def save_instagram_data():
    # Accept form-encoded (e.g., Twilio) or JSON payloads
    data = request.form if request.form else (request.get_json(silent=True) or {})
    message = data.get('Body') if isinstance(data, dict) or hasattr(data, 'get') else None
    if not message:
        # try values as a last resort
        message = request.values.get('Body')
    instagram_reel = extract_instagram_url(message)
    # Here you would typically save the data to a database
    
    # Convert ImmutableMultiDict to a regular dict for logging
    try:
        logged = dict(data)
    except Exception:
        logged = data
    print("Received Instagram data:", logged)
    print("Extracted Instagram URL:", instagram_reel)

    return jsonify({
        "status": "success",
        "message": "Instagram data saved successfully!",
        "instagram_url": instagram_reel
    }), 200
