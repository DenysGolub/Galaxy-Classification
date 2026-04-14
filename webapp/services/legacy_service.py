import requests

class LegacyService:
    @staticmethod
    def get_legacy_data(ra, dec):
        """Fetch legacy astronomical data from NOIRLab TAP service"""
        if not ra or not dec:
            return {"sources": []}, 400

        try:
            # Use the official TAP service for DR10 - much more reliable than the viewer URL
            # We query for objects within a 5 arcsecond radius (0.0014 degrees)
            query = f"SELECT TOP 1 type, flux_g, flux_r, ra, dec FROM ls_dr10.tractor WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, 0.0014)) = 1"
            tap_url = f"https://datalab.noirlab.edu/tap/sync?request=doQuery&lang=ADQL&format=json&query={requests.utils.quote(query)}"

            resp = requests.get(tap_url, timeout=10)

            if resp.status_code != 200:
                return {"sources": [], "error": "Upstream service error"}, 200

            data = resp.json()

            # DataLab TAP format returns results in data['table']['rows']
            sources = []
            if 'table' in data and 'rows' in data['table']:
                for row in data['table']['rows']:
                    sources.append({
                        "type": row[0],
                        "flux_g": row[1],
                        "flux_r": row[2],
                        "ra": row[3],
                        "dec": row[4]
                    })

            return {"sources": sources}, 200

        except Exception as e:
            print(f"LEGACY ERROR: {e}")
            return {"sources": [], "error": str(e)}, 200