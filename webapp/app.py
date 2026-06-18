import os
import sys
import threading
from flask import Flask
from flask_cors import CORS
import webview

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

from webapp.routes import register_all_routes

app = Flask(__name__)
CORS(app)

register_all_routes(app)


def run_flask():
    app.run(debug=True, use_reloader=False)


def main():
   run_flask()


if __name__ == '__main__':
    main()
