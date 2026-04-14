from flask import request, jsonify
from galaxy_classification.database import GalaxyDatabase
from webapp.services.prediction_service import PredictionService

prediction_service = PredictionService()
db = GalaxyDatabase()

def register_prediction_routes(app):
    @app.route('/predict', methods=['POST'])
    def predict():
        """Predict galaxy morphology from image"""
        print("SIGNAL RECEIVED: Processing frame...") # Debug log
        try:
            data = request.json['image']

            # Generate observation ID
            observation_id = prediction_service.generate_observation_id()

            # For now, use dummy coordinates (would come from frontend)
            ra = request.json.get('ra', 0.0)
            dec = request.json.get('dec', 0.0)
            survey_source = request.json.get('survey', 'DESI DR10')
            fov = request.json.get('fov')

            # Save observation to database
            obs_db_id = db.save_observation(observation_id, ra, dec, survey_source, data, fov)

            # Make prediction
            result = prediction_service.predict_galaxy(data)
            result["observation_id"] = observation_id

            print(f"ANALYSIS COMPLETE: {result['prediction']}")
            return jsonify(result)

        except Exception as e:
            print(f"CORE ERROR: {str(e)}")
            return jsonify({"error": str(e), "status": "fail"}), 400