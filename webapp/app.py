import os
import sys
from flask import Flask
from flask_cors import CORS

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

# Import route registrars
from webapp.routes import register_all_routes

# Create Flask app
app = Flask(__name__)
CORS(app)

# Register all routes
register_all_routes(app)

def main():
    """Main entry point for the Flask application"""
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    main()