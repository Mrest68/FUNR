from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.routes.date_routes import date_bp
    from app.routes.instagram_routes import instagram_bp
    
    app.register_blueprint(date_bp, url_prefix='/api')
    app.register_blueprint(instagram_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return {"message": "FUNR Backend API is running!"}, 200
    
    return app
