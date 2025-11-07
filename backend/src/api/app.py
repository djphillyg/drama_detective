"""Flask application factory."""
import os
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "https://frontend-production-4e88.up.railway.app",
                os.getenv("FRONTEND_URL", "")
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Register routes
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    return app
