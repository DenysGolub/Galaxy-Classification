from flask import request, jsonify, Response
from galaxy_classification.database import GalaxyDatabase

db = GalaxyDatabase()

def register_observation_routes(app):
    @app.route('/api/observations', methods=['GET'])
    def get_observations():
        """Get recent observations for the dossier page"""
        limit = int(request.args.get('limit', 20))
        observations = db.get_recent_observations(limit)

        # Convert to format expected by frontend
        result = []
        for obs in observations:
            result.append({
                'id': obs['observation_id'],
                'coordinates': f"{obs['ra']:.5f}, {obs['dec']:.5f}",
                'classification': obs['predicted_class'],
                'confidence': f"{obs['confidence']*100:.1f}%",
                'has_image': obs['has_image']
            })

        return jsonify(result)

    @app.route('/api/observation/<observation_id>', methods=['GET'])
    def get_observation(observation_id):
        """Get detailed observation data"""
        obs = db.get_observation_by_id(observation_id)
        if obs:
            return jsonify(obs)
        return jsonify({"error": "Observation not found"}), 404

    @app.route('/api/observation/<observation_id>/classify', methods=['POST'])
    def classify_observation(observation_id):
        """Save or update classification for an observation."""
        data = request.json or {}
        predicted_class = data.get('predicted_class')
        confidence = data.get('confidence')
        model_version = data.get('model_version', 'best_0.8200.pth')
        is_manual = data.get('is_manual', False)
        manual_class = data.get('manual_class') if is_manual else None

        if not predicted_class or confidence is None:
            return jsonify({"error": "Missing classification data"}), 400

        observation_internal_id = db.get_observation_internal_id(observation_id)
        if observation_internal_id is None:
            return jsonify({"error": "Observation not found"}), 404

        db.save_or_update_classification(
            observation_internal_id,
            model_version,
            predicted_class,
            confidence,
            is_manual=is_manual,
            manual_class=manual_class
        )

        if is_manual:
            db.save_user_feedback(
                observation_internal_id,
                data.get('original_prediction', predicted_class),
                predicted_class,
                'correction',
                data.get('comments')
            )

        return jsonify({"status": "classified"})

    @app.route('/api/observation/<observation_id>/image', methods=['GET'])
    def get_observation_image(observation_id):
        """Serve stored observation image"""
        image_data = db.get_image_data(observation_id)
        if image_data:
            return Response(image_data, mimetype='image/jpeg')
        return jsonify({"error": "Image not found"}), 404

    @app.route('/api/observation/<observation_id>/delete', methods=['DELETE'])
    def delete_observation(observation_id):
        """Delete a single observation and related records"""
        deleted = db.delete_observation(observation_id)
        if deleted:
            return jsonify({"status": "deleted"})
        return jsonify({"error": "Observation not found"}), 404

    @app.route('/api/observations/purge', methods=['DELETE'])
    def purge_observations():
        """Delete all observations and related records"""
        db.delete_all_observations()
        return jsonify({"status": "purged"})