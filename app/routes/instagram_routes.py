import flask
import re
from flask import Blueprint, request, jsonify
from datetime import datetime
from openai import OpenAI
import instaloader
import os


instagram_bp = Blueprint('instagram', __name__)

# Initialize OpenAI client (new API format)
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("❌ OPENAI_API_KEY is not set in the environment!")

client = OpenAI(api_key=openai_api_key)

instagram_username = os.getenv("INSTAGRAM_USERNAME")
instagram_password = os.getenv("INSTAGRAM_PASSWORD")


def extract_instagram_url(text):
    if not text:
        return None
    
    pattern = r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels|stories|[a-zA-Z0-9._]+)(?:/[a-zA-Z0-9._/-]+)?"
    
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        url = match.group(0)
        url = url.rstrip('.,;:!?)')
        return url
    return None

def extract_shortcode_from_url(instagram_url):
    """Extract shortcode from Instagram URL (needed for instaloader)"""
    if not instagram_url:
        return None
    
    # Pattern to extract shortcode from /p/ or /reel/ URLs
    pattern = r"instagram\.com/(?:p|reel|reels)/([a-zA-Z0-9_-]+)"
    match = re.search(pattern, instagram_url, re.IGNORECASE)
    
    if match:
        return match.group(1)
    return None

def get_instagram_caption(instagram_url):
    """Fetch the caption from an Instagram post/reel"""
    try:
        shortcode = extract_shortcode_from_url(instagram_url)
        if not shortcode:
            print("❌ No shortcode found in URL")
            return None
        
        print(f"🔑 Extracted shortcode: {shortcode}")
        
        # Initialize instaloader
        L = instaloader.Instaloader()
        
        L.download_video = False
        L.download_comments = False
        L.download_geotags = False  
        # Login if credentials are provided (helps avoid rate limits)
        if instagram_username and instagram_password:
            session_file = f"{instagram_username}.session"
            try:
                print(f"🔐 Loading session for {instagram_username}...")
                L.load_session_from_file(instagram_username)
                print("✅ Session loaded successfully!")
            except FileNotFoundError:
                print(f"🔐 No session found, logging in as {instagram_username}...")
                L.login(instagram_username, instagram_password)
                L.save_session_to_file(session_file)
                print("✅ Login successful and session saved!")
        
        # Get post by shortcode
        print(f"📥 Fetching post data for shortcode: {shortcode}")
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Extract caption and tagged users
        caption = post.caption if post.caption else ""
        tagged_users = [user.username for user in post.tagged_users] if post.tagged_users else []
        location = post.location.name if post.location else None
        
        print(f"✅ Successfully fetched Instagram data")
        
        return {
            "caption": caption,
            "tagged_users": tagged_users,
            "location": location
        }
    
    except Exception as e:
        print(f"❌ Error fetching Instagram data: {type(e).__name__}: {e}")
        return None

def extract_restaurant_name_with_ai(caption, tagged_users, location):
    """Use OpenAI to extract restaurant name from caption, tags, and location"""
    try:
        if not client.api_key:
            print("❌ OpenAI API key not found")
            return "Unknown"
        
        prompt = f"""
        Extract the restaurant name from the following Instagram reel data:
        
        Caption: {caption}
        Tagged Users: {', '.join(tagged_users) if tagged_users else 'None'}
        Location: {location if location else 'None'}
        
        Return ONLY the restaurant name, nothing else. If no restaurant is mentioned, return "Unknown".
        """
        
        print("🤖 Calling OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts restaurant names from Instagram captions and metadata."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0
        )
        
        restaurant_name = response.choices[0].message.content.strip()
        print(f"✅ OpenAI extracted: {restaurant_name}")
        return restaurant_name
    
    except Exception as e:
        print(f"❌ Error with OpenAI: {type(e).__name__}: {e}")
        return "Unknown"

def extract_restuarant(instagram_url):
    if not instagram_url:
        return None
    
    pattern = r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)(?:/)?"
    
    match = re.search(pattern, instagram_url, re.IGNORECASE)
    if match:
        username = match.group(1)
        return username
    return None

@app.route("/env-check")
def env_check():
    return {
        "OPENAI_API_KEY_set": bool(os.getenv("OPENAI_API_KEY")),
        "INSTAGRAM_USERNAME_set": bool(os.getenv("INSTAGRAM_USERNAME"))
    }

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

    data = {}

    if request.form:
        data = request.form.to_dict()
    elif request.is_json:
        data = request.get_json(silent=True) or {}
    if not data:
        data = request.values.to_dict()

    message = data.get("Body", "")
    instagram_url = extract_instagram_url(message)

    print("📩 Received Instagram data:", data)
    print("📝 Message Body:", repr(message))
    print("🔗 Extracted Instagram URL:", instagram_url)

    if not instagram_url:
        return jsonify({
            "status": "error",
            "message": "No Instagram URL found in message"
        }), 400

    # Fetch Instagram caption and metadata
    instagram_data = get_instagram_caption(instagram_url)
    
    restaurant_name = "Unknown"
    caption = None
    tagged_users = []
    location = None
    
    if instagram_data:
        caption = instagram_data["caption"]
        tagged_users = instagram_data["tagged_users"]
        location = instagram_data["location"]
        
        print("📸 Caption:", caption)
        print("👥 Tagged Users:", tagged_users)
        print("📍 Location:", location)
        
        # Extract restaurant name using AI
        restaurant_name = extract_restaurant_name_with_ai(
            caption,
            tagged_users,
            location
        )
        print("🍽️ Restaurant Name:", restaurant_name)

    return jsonify({
        "status": "success",
        "message": "Instagram data saved successfully!",
        "instagram_url": instagram_url,
        "text_message": message,
        "caption": caption,
        "tagged_users": tagged_users,
        "location": location,
        "restaurant_name": restaurant_name
    }), 200