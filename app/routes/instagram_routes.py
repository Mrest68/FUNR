import flask
import re
from flask import Blueprint, request, jsonify
from datetime import datetime
from openai import OpenAI
import requests
import os


instagram_bp = Blueprint('instagram', __name__)

# Initialize OpenAI client and Apify token
openai_api_key = os.getenv("OPENAI_API_KEY")
apify_api_token = os.getenv("APIFY_API_TOKEN")

if not openai_api_key:
    raise RuntimeError("❌ OPENAI_API_KEY is not set in the environment!")
if not apify_api_token:
    raise RuntimeError("❌ APIFY_API_TOKEN is not set in the environment!")

client = OpenAI(api_key=openai_api_key)




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

def get_instagram_caption(instagram_url):
    """Fetch the caption from an Instagram post/reel using Apify API"""
    try:
        print(f"🚀 Calling Apify Instagram Scraper for: {instagram_url}")
        
        # Apify API endpoint - Run Actor synchronously and get dataset items
        apify_url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items?token={apify_api_token}"
        
        # Request payload
        payload = {
            "directUrls": [instagram_url],
            "resultsLimit": 1,
            "resultsType": "posts",
            "proxy": {"useApifyProxy": True}
        }
        
        # Make POST request to Apify
        response = requests.post(
            apify_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # Wait up to 2 minutes for scraping
        )
        
        if response.status_code != 200:
            print(f"❌ Apify API error: {response.status_code} - {response.text}")
            return None
        
        # Parse response (returns array of scraped items)
        data = response.json()
        
        if not data or len(data) == 0:
            print("❌ No data returned from Apify")
            return None
        
        post_data = data[0]
        print(f"📦 Raw Apify data keys: {post_data.keys()}")
        
        # Extract relevant information from Apify response
        caption = post_data.get("caption", "")
        
        # Tagged users might be in different fields depending on Apify version
        tagged_users = []
        if "taggedUsers" in post_data:
            tagged_users = [user.get("username") for user in post_data.get("taggedUsers", []) if user.get("username")]
        elif "mentions" in post_data:
            tagged_users = [mention.get("username") for mention in post_data.get("mentions", []) if mention.get("username")]
        
        location = post_data.get("locationName") or (post_data.get("location", {}).get("name") if isinstance(post_data.get("location"), dict) else None)
        
        print(f"✅ Successfully fetched Instagram data via Apify")
        
        return {
            "caption": caption,
            "tagged_users": tagged_users,
            "location": location
        }
    
    except requests.exceptions.Timeout:
        print("❌ Apify request timed out (scraping took too long)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error calling Apify: {e}")
        return None
    except Exception as e:
        print(f"❌ Error calling Apify API: {type(e).__name__}: {e}")
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
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract restaurant names from IG content."},
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

@instagram_bp.route("/env-check")
def env_check():
    return {
        "OPENAI_API_KEY_set": bool(os.getenv("OPENAI_API_KEY")),
        "APIFY_API_TOKEN_set": bool(os.getenv("APIFY_API_TOKEN"))
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
    else:
        print("⚠️ Could not fetch Instagram data from Apify")
        print("💡 Tip: User can send caption in a follow-up message")

    return jsonify({
        "status": "success",
        "message": "Instagram URL received! " + (
            "Caption extracted successfully." if instagram_data 
            else "Could not fetch caption. Please send the restaurant name in your next message."
        ),
        "instagram_url": instagram_url,
        "text_message": message,
        "caption": caption,
        "tagged_users": tagged_users,
        "location": location,
        "restaurant_name": restaurant_name,
        "needs_manual_caption": instagram_data is None
    }), 200