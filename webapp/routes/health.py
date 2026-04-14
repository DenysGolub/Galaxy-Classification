from flask import jsonify
from galaxy_classification.database import GalaxyDatabase

db = GalaxyDatabase()

def register_health_routes(app):
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            stats = db.get_classification_stats()
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "records": len(stats)
            })
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 500