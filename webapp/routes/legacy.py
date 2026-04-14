from flask import request, jsonify
from webapp.services.legacy_service import LegacyService

def register_legacy_routes(app):
    @app.route('/legacy')
    def get_legacy_data():
        """Get legacy astronomical data"""
        ra = request.args.get('ra')
        dec = request.args.get('dec')

        result, status_code = LegacyService.get_legacy_data(ra, dec)
        return jsonify(result), status_code