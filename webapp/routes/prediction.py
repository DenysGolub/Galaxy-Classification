from flask import request, jsonify
from galaxy_classification.database import GalaxyDatabase
from webapp.services.prediction_service import PredictionService
from astroquery.sdss import SDSS
from astropy import coordinates as coords
import astropy.units as u

prediction_service = PredictionService()
db = GalaxyDatabase()

def gather_sdss_metadata(ra, dec):
    """
    Gather SDSS metadata for given RA/DEC coordinates.
    Similar to the gather_metadata.ipynb notebook.
    """
    metadata = {}
    
    try:
        # 1. Check for default/empty coords
        if ra == 0.0 and dec == 0.0:
            return {"error": "Invalid coordinates (0,0) provided."}

        pos = coords.SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        
        # 2. Increase radius to 10 arcsec for better hit rates
        search_radius = 30 * u.arcsec
        
        # 3. Specify data_release (e.g., DR16 is very stable)
        # Query photometric data
        phot_result = SDSS.query_region(
            pos, 
            radius=search_radius,
            data_release=19, 
            photoobj_fields=["objid", "ra", "dec", "u", "g", "r", "i", "z", "type", "petroR50_r", "petroR90_r", "flags"]
        )
        
        # Query spectroscopic data
        spec_result = SDSS.query_region(
            pos, 
            radius=search_radius,
            data_release=19,
            specobj_fields=["specobjid", "z", "velDisp", "class", "subClass", "plate", "mjd", "fiberID"]
        )
        
        if phot_result is not None and len(phot_result) > 0:
            row = phot_result[0]
            metadata.update({
                "phot_objid": int(row["objid"]) if row.get("objid") is not None else None,
                "phot_ra": float(row["ra"]),
                "phot_dec": float(row["dec"]),
                "phot_type": str(row["type"]) if row.get("type") is not None else None,
                "u_mag": float(row["u"]),
                "g_mag": float(row["g"]),
                "r_mag": float(row["r"]),
                "i_mag": float(row["i"]),
                "z_mag": float(row["z"]),
                "petroR50_r": float(row.get("petroR50_r")) if row.get("petroR50_r") is not None else None,
                "petroR90_r": float(row.get("petroR90_r")) if row.get("petroR90_r") is not None else None,
                "flags": int(row.get("flags")) if row.get("flags") is not None else None
            })
            print("[METADATA] Photometric data retrieved")
        else:
            print("[METADATA] No photometric data found")
        
        if spec_result is not None and len(spec_result) > 0:
            row = spec_result[0]
            metadata.update({
                "specobjid": int(row["specobjid"]) if row.get("specobjid") is not None else None,
                "z": float(row["z"]) if row["z"] is not None else None,
                "velDisp": float(row.get("velDisp")) if row.get("velDisp") is not None else None,
                "class": str(row.get("class")) if row.get("class") is not None else None,
                "subClass": str(row.get("subClass")) if row.get("subClass") is not None else None,
                "plate": int(row.get("plate")) if row.get("plate") is not None else None,
                "mjd": int(row.get("mjd")) if row.get("mjd") is not None else None,
                "fiberID": int(row.get("fiberID")) if row.get("fiberID") is not None else None
            })
            print("[METADATA] Spectroscopic data retrieved")
        else:
            print("[METADATA] No spectroscopic data found")
        
        print("[METADATA] Full metadata gathered:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"[METADATA] Error gathering metadata: {str(e)}")
        metadata["error"] = str(e)
    
    return metadata

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

    @app.route('/metadata', methods=['POST'])
    def get_metadata():
        """Get SDSS metadata for given coordinates"""
        try:
            ra = request.json.get('ra', 0.0)
            dec = request.json.get('dec', 0.0)
            
            metadata = gather_sdss_metadata(ra, dec)
            return jsonify(metadata)
            
        except Exception as e:
            print(f"[METADATA] Error in get_metadata endpoint: {str(e)}")
            return jsonify({"error": str(e), "status": "fail"}), 400