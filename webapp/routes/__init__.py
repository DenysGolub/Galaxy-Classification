from flask import app, render_template, request, send_file, send_from_directory
from .prediction import register_prediction_routes
from .legacy import register_legacy_routes
from .observations import register_observation_routes
from .stats import register_stats_routes
from .chat import register_chat_routes
from .health import register_health_routes
from galaxy_classification.database import GalaxyDatabase
from io import BytesIO
import os
import re
import asyncio
from datetime import datetime

pdf_db = GalaxyDatabase()

def sanitize_filename(name: str) -> str:
    name = os.path.basename(name or '')
    name = re.sub(r'[^A-Za-z0-9._-]', '_', name)
    if not name.lower().endswith('.pdf'):
        name += '.pdf'
    return name


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

    @app.route('/report')
    def report_page():
        return render_template('report.html')

    @app.route('/report/download')
    def download_report():
        observation_id = request.args.get('id')
        if not observation_id:
            return {"error": "Missing report id"}, 400

        observation = pdf_db.get_observation_by_id(observation_id)
        if not observation:
            return {"error": "Observation not found"}, 404

        filename = sanitize_filename(request.args.get('filename', '').strip() or f'gcs-report-{observation_id}.pdf')

        # Generate PDF by screenshotting the report page
        report_url = f"http://127.0.0.1:5000/report?id={observation_id}"
        try:
            pdf_bytes = asyncio.run(generate_pdf_from_page(report_url))
        except Exception as exc:
            return {"error": "Report PDF generation failed", "details": str(exc)}, 500

        return send_file(BytesIO(pdf_bytes), as_attachment=True, download_name=filename, mimetype='application/pdf')

    @app.route('/ping')
    def ping():
        # You can even trigger model loading here if it's not global
        return {"status": "online"}, 200

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                            'favicon.ico',mimetype='image/vnd.microsoft.icon')
