from flask import request, jsonify
from galaxy_classification.database import GalaxyDatabase

db = GalaxyDatabase()

def register_stats_routes(app):
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get classification statistics"""
        stats = db.get_classification_stats()
        return jsonify(stats)

    @app.route('/api/feedback', methods=['POST'])
    def save_feedback():
        """Save user feedback/correction"""
        data = request.json or {}
        observation_id = data.get('observation_id')
        original_prediction = data.get('original_prediction')
        user_correction = data.get('user_correction')
        feedback_type = data.get('feedback_type', 'correction')
        comments = data.get('comments')

        if not all([observation_id, original_prediction, user_correction]):
            return jsonify({"error": "Missing required fields"}), 400

        internal_id = db.get_observation_internal_id(observation_id)
        if internal_id is None:
            return jsonify({"error": "Observation not found"}), 404

        db.save_user_feedback(internal_id, original_prediction, user_correction,
                             feedback_type, comments)
        db.save_classification(internal_id, 'best_0.8200.pth', user_correction,
                              1.0, is_manual=True, manual_class=user_correction)
        return jsonify({"status": "success"})