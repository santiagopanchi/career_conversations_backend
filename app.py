"""Main Flask application."""
from flask import Flask
from flask_cors import CORS
from config import get_env
from me import Me
from routes import register_routes

app = Flask(__name__)
CORS(app)

# Initialize once at process start
me = Me()

# Register all routes
register_routes(app, me)

if __name__ == "__main__":
    # Default to port 8000 for local dev
    port = int(get_env("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)