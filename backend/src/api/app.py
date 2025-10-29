"""Flask application factory."""
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "https://drama-detective.railway.app"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Register routes
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    return app
