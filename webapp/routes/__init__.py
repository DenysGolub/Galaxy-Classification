from flask import render_template
from .prediction import register_prediction_routes
from .legacy import register_legacy_routes
from .observations import register_observation_routes
from .stats import register_stats_routes
from .chat import register_chat_routes
from .health import register_health_routes

def register_all_routes(app):
    """Register all route handlers with the Flask app"""

    # Register API routes
    register_prediction_routes(app)
    register_legacy_routes(app)
    register_observation_routes(app)
    register_stats_routes(app)
    register_chat_routes(app)
    register_health_routes(app)

    # Register page routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/assistant')
    def assistant_page():
        return render_template('assistant.html')

    @app.route('/dossier')
    def dossier_page():
        return render_template('dossier.html')

    @app.route('/survey')
    def survey_page():
        return render_template('survey.html')