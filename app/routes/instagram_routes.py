import flask
import re
from flask import Blueprint, request, jsonify
from datetime import datetime

instagram_bp = Blueprint('instagram', __name__)

def extract_instagram_url(text):
    if not text:
        return None
    
    # Pattern to match Instagram URLs for posts, reels, profiles, stories, etc.
    # Handles both http/https and with/without www
    # Stops at whitespace or common punctuation that's not part of URLs
    pattern = r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels|stories|[a-zA-Z0-9._]+)(?:/[a-zA-Z0-9._/-]+)?"
    
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        url = match.group(0)
        # Remove trailing punctuation that's not typically part of URLs
        url = url.rstrip('.,;:!?)')
        return url
    return None


@instagram_bp.route('/save-instagram-data', methods=['POST'])
def save_instagram_data():

    # Debug: Log all request details
    print("=" * 50)
    print("Content-Type:", request.content_type)
    print("request.form:", dict(request.form))
    print("request.get_json():", request.get_json(silent=True))
    print("request.data:", request.data)
    print("request.values:", dict(request.values))
    print("=" * 50)

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
    print("📝 Message Body:", repr(message))
    print("🔗 Extracted Instagram URL:", instagram_url)

    return jsonify({
        "status": "success",
        "message": "Instagram data saved successfully!",
        "instagram_url": instagram_url,
        "text_message": message
        
    }), 200
