import flask
import re
from flask import Blueprint, request, jsonify
from datetime import datetime

instagram_bp = Blueprint('instagram', __name__)

def extract_instagram_url(text):
    if not text:
        return None
    pattern = r"(https?://(?:www\.)?instagram\.com/[^\s]+)"
    match = re.search(pattern, text)
    return match.group(0) if match else None


@instagram_bp.route('/save-instagram-data', methods=['POST'])
def save_instagram_data():

    # Twilio sends POST as x-www-form-urlencoded
    # Postman/TailEnd may send form-data or JSON
    data = {}

    # Priority 1: Twilio/Form-Encoded
    if request.form:
        data = request.form.to_dict()

    # Priority 2: JSON
    elif request.is_json:
        data = request.get_json(silent=True) or {}

    # Priority 3: Anything else (final fallback)
    if not data:
        data = request.values.to_dict()

    # Body is where Twilio sends SMS text
    message = data.get("Body", "")

    instagram_url = extract_instagram_url(message)

    print("📩 Received Instagram data:", data)
    print("🔗 Extracted Instagram URL:", instagram_url)

    return jsonify({
        "status": "success",
        "message": "Instagram data saved successfully!",
        "instagram_url": instagram_url
    }), 200
