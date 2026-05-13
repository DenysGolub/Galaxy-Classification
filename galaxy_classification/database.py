import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import base64
from io import BytesIO
from PIL import Image

class GalaxyDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(root_dir, 'galaxy_classification.db')
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database with schema"""
        schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'galaxy-classification/config', 'database_schema.sql'))
        with open(schema_path, 'r') as f:
            schema = f.read()

        conn = self.get_connection()
        try:
            conn.executescript(schema)
            conn.commit()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
        finally:
            conn.close()

    # Observation management 
    def save_observation(self, observation_id: str, ra: float, dec: float,
                        survey_source: str, image_data: str = None,
                        fov: float = None) -> int:
        """Save a new galaxy observation"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Convert base64 image to blob if provided
            image_blob = None
            if image_data and image_data.startswith('data:image'):
                header, encoded = image_data.split(",", 1)
                image_blob = base64.b64decode(encoded)

            cursor.execute("""
                INSERT INTO observations (observation_id, ra, dec, survey_source,
                                        image_data, fov)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (observation_id, ra, dec, survey_source, image_blob, fov))

            observation_db_id = cursor.lastrowid
            conn.commit()
            return observation_db_id
        finally:
            conn.close()

    def save_classification(self, observation_id: int, model_version: str,
                          predicted_class: str, confidence: float,
                          is_manual: bool = False, manual_class: str = None) -> int:
        """Save classification result"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO classifications (observation_id, model_version,
                                           predicted_class, confidence,
                                           is_manual_override, manual_class)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (observation_id, model_version, predicted_class, confidence,
                  is_manual, manual_class))

            classification_id = cursor.lastrowid
            conn.commit()
            return classification_id
        finally:
            conn.close()

    def save_or_update_classification(self, observation_id: int, model_version: str,
                                      predicted_class: str, confidence: float,
                                      is_manual: bool = False, manual_class: str = None) -> int:
        """Insert or update classification for an observation."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM classifications WHERE observation_id = ?
            """, (observation_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    UPDATE classifications
                    SET model_version = ?, predicted_class = ?, confidence = ?,
                        is_manual_override = ?, manual_class = ?
                    WHERE observation_id = ?
                """, (model_version, predicted_class, confidence,
                      is_manual, manual_class, observation_id))
                conn.commit()
                return row[0]

            cursor.execute("""
                INSERT INTO classifications (observation_id, model_version,
                                           predicted_class, confidence,
                                           is_manual_override, manual_class)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (observation_id, model_version, predicted_class, confidence,
                  is_manual, manual_class))
            classification_id = cursor.lastrowid
            conn.commit()
            return classification_id
        finally:
            conn.close()

    def save_astronomical_metadata(self, observation_id: int, catalog_source: str,
                                 metadata: dict):
        """Save astronomical metadata from external catalogs"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO astronomical_metadata
                (observation_id, catalog_source, object_type, flux_g, flux_r,
                 redshift, u_magnitude, g_magnitude, r_magnitude, i_magnitude,
                 z_magnitude, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observation_id,
                catalog_source,
                metadata.get('class') or metadata.get('type') or metadata.get('phot_type'),
                metadata.get('flux_g'),
                metadata.get('flux_r'),
                metadata.get('redshift') if metadata.get('redshift') is not None else metadata.get('z'),
                metadata.get('u') if metadata.get('u') is not None else metadata.get('u_mag'),
                metadata.get('g') if metadata.get('g') is not None else metadata.get('g_mag'),
                metadata.get('r') if metadata.get('r') is not None else metadata.get('r_mag'),
                metadata.get('i') if metadata.get('i') is not None else metadata.get('i_mag'),
                metadata.get('z_mag'),
                json.dumps(metadata)
            ))
            conn.commit()
        finally:
            conn.close()

    # Chat management
    def start_chat_session(self, session_id: str, title: str = None) -> int:
        """Start a new chat session"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_sessions (session_id, title)
                VALUES (?, ?)
            """, (session_id, title))

            session_db_id = cursor.lastrowid
            conn.commit()
            return session_db_id
        finally:
            conn.close()

    def save_chat_message(self, session_id: int, role: str, content: str,
                         tokens_used: int = None):
        """Save a chat message"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_messages (session_id, role, content, tokens_used)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, tokens_used))
            conn.commit()
        finally:
            conn.close()

    def get_chat_history(self, session_id: int, limit: int = 50) -> List[Dict]:
        """Get chat history for a session"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, timestamp
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (session_id, limit))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'role': row[0],
                    'content': row[1],
                    'timestamp': row[2]
                })
            return messages
        finally:
            conn.close()

    def get_chat_sessions(self, limit: int = 50) -> List[Dict]:
        """List existing chat sessions."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, title, started_at
                FROM chat_sessions
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'title': row[1] or 'Untitled Session',
                    'started_at': row[2]
                })
            return sessions
        finally:
            conn.close()

    # Query methods
    def get_recent_observations(self, limit: int = 20) -> List[Dict]:
        """Get recent observations with classifications"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.observation_id, o.ra, o.dec, o.survey_source,
                       c.predicted_class, c.confidence, c.classified_at,
                       o.image_data
                FROM observations o
                LEFT JOIN classifications c ON o.id = c.observation_id
                WHERE c.id IS NOT NULL
                ORDER BY c.classified_at DESC
                LIMIT ?
            """, (limit,))

            observations = []
            for row in cursor.fetchall():
                obs = {
                    'observation_id': row[0],
                    'ra': row[1],
                    'dec': row[2],
                    'survey_source': row[3],
                    'predicted_class': row[4],
                    'confidence': row[5],
                    'classified_at': row[6],
                    'has_image': row[7] is not None
                }
                observations.append(obs)
            return observations
        finally:
            conn.close()

    def get_observation_count(self) -> int:
        """Return the number of captured observations."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM observations")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_classified_observation_count(self) -> int:
        """Return the number of observations with a classification."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT observation_id)
                FROM classifications
            """)
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_latest_observation_id(self) -> Optional[str]:
        """Return the latest captured observation id."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT observation_id
                FROM observations
                ORDER BY captured_at DESC, id DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def get_observation_by_id(self, observation_id: str) -> Optional[Dict]:
        """Get full observation details by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, c.predicted_class, c.confidence, c.model_version,
                       c.is_manual_override, c.manual_class,
                       am.object_type, am.flux_g, am.flux_r, am.redshift,
                       am.u_magnitude, am.g_magnitude, am.r_magnitude,
                       am.i_magnitude, am.z_magnitude, am.catalog_source,
                       am.metadata_json, am.retrieved_at
                FROM observations o
                LEFT JOIN classifications c ON o.id = c.observation_id
                LEFT JOIN astronomical_metadata am ON o.id = am.observation_id
                WHERE o.observation_id = ?
            """, (observation_id,))

            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'observation_id': row[1],
                    'ra': row[2],
                    'dec': row[3],
                    'survey_source': row[4],
                    'image_path': row[5],
                    'image_data': base64.b64encode(row[6]).decode('utf-8') if row[6] else None,  # blob data as base64
                    'captured_at': row[7],
                    'fov': row[8],
                    'predicted_class': row[9],
                    'confidence': row[10],
                    'model_version': row[11],
                    'is_manual_override': row[12],
                    'manual_class': row[13],
                    'object_type': row[14],
                    'flux_g': row[15],
                    'flux_r': row[16],
                    'redshift': row[17],
                    'u_magnitude': row[18],
                    'g_magnitude': row[19],
                    'r_magnitude': row[20],
                    'i_magnitude': row[21],
                    'z_magnitude': row[22],
                    'metadata_catalog_source': row[23],
                    'metadata_json': json.loads(row[24]) if row[24] else None,
                    'metadata_retrieved_at': row[25]
                }
            return None
        finally:
            conn.close()

    def find_by_id_or_name(self, identifier: str) -> Optional[Dict]:
        """Find an observation by exact ID or partial identifier search."""
        observation = self.get_observation_by_id(identifier)
        if observation:
            return observation

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, c.predicted_class, c.confidence, c.model_version,
                       c.is_manual_override, c.manual_class,
                       am.object_type, am.flux_g, am.flux_r, am.redshift
                FROM observations o
                LEFT JOIN classifications c ON o.id = c.observation_id
                LEFT JOIN astronomical_metadata am ON o.id = am.observation_id
                WHERE o.observation_id LIKE ?
                LIMIT 1
            """, (f'%{identifier}%',))

            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'observation_id': row[1],
                    'ra': row[2],
                    'dec': row[3],
                    'survey_source': row[4],
                    'image_data': row[7],
                    'captured_at': row[8],
                    'fov': row[9],
                    'predicted_class': row[11],
                    'confidence': row[12],
                    'model_version': row[13],
                    'is_manual_override': row[14],
                    'manual_class': row[15],
                    'object_type': row[16],
                    'flux_g': row[17],
                    'flux_r': row[18],
                    'redshift': row[19]
                }
            return None
        finally:
            conn.close()

    def get_classification_stats(self) -> List[Dict]:
        """Get classification statistics"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT predicted_class, COUNT(*), AVG(confidence),
                       MIN(confidence), MAX(confidence)
                FROM classifications
                GROUP BY predicted_class
                ORDER BY COUNT(*) DESC
            """)

            stats = []
            for row in cursor.fetchall():
                stats.append({
                    'class': row[0],
                    'count': row[1],
                    'avg_confidence': row[2],
                    'min_confidence': row[3],
                    'max_confidence': row[4]
                })
            return stats
        finally:
            conn.close()

    def get_recent_observations_summary(self, limit: int = 5) -> str:
        """Build a concise summary of recent observations from the local database."""
        observations = self.get_recent_observations(limit)
        if not observations:
            return "No recent classified observations are available in the local database."

        lines = []
        for obs in observations:
            lines.append(
                f"- {obs['observation_id']} | RA={obs['ra']:.3f} DEC={obs['dec']:.3f} | "
                f"survey={obs['survey_source']} | class={obs['predicted_class']} "
                f"({obs['confidence']:.2f})"
            )
        return "\n".join(lines)

    def get_observation_summary(self, observation_id: str) -> Optional[Dict]:
        """Get a compact summary for a named observation."""
        observation = self.get_observation_by_id(observation_id)
        if observation is None:
            return None

        return {
            'observation_id': observation['observation_id'],
            'ra': observation['ra'],
            'dec': observation['dec'],
            'survey_source': observation['survey_source'],
            'predicted_class': observation.get('predicted_class'),
            'confidence': observation.get('confidence'),
            'redshift': observation.get('redshift'),
            'object_type': observation.get('object_type')
        }

    def get_observation_internal_id(self, observation_id: str) -> Optional[int]:
        """Return the internal database id for an observation."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM observations WHERE observation_id = ?
            """, (observation_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def get_or_create_chat_session(self, session_id: str, title: str = None) -> int:
        """Return the chat session PK for a session identifier."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM chat_sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row:
                return row[0]

            cursor.execute("""
                INSERT INTO chat_sessions (session_id, title)
                VALUES (?, ?)
            """, (session_id, title))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def delete_observation(self, observation_id: str) -> bool:
        """Delete an observation and its dependent records."""
        obs_id = self.get_observation_internal_id(observation_id)
        if obs_id is None:
            return False

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_feedback WHERE observation_id = ?", (obs_id,))
            cursor.execute("DELETE FROM astronomical_metadata WHERE observation_id = ?", (obs_id,))
            cursor.execute("DELETE FROM classifications WHERE observation_id = ?", (obs_id,))
            cursor.execute("DELETE FROM observations WHERE id = ?", (obs_id,))
            conn.commit()
            return True
        finally:
            conn.close()
            
            
    def get_sample_rows(self, limit=5):

        query = """
        SELECT
            o.observation_id,
            o.ra,
            o.dec,
            o.survey_source,
            c.predicted_class,
            c.confidence,
            m.object_type,
            m.redshift
        FROM observations o
        LEFT JOIN classifications c
            ON o.id = c.observation_id
        LEFT JOIN astronomical_metadata m
            ON o.id = m.observation_id
        LIMIT ?
        """

        try:

            cursor = self.conn.cursor()

            cursor.execute(query, (limit,))

            rows = cursor.fetchall()

            columns = [
                description[0]
                for description in cursor.description
            ]

            formatted_rows = []

            for row in rows:

                formatted_rows.append(
                    dict(zip(columns, row))
                )

            return json.dumps(
                formatted_rows,
                indent=2,
                default=str
            )

        except Exception as e:
            return f"Failed to fetch sample rows: {str(e)}"

    def get_schema_info(self) -> str:
        """Return database schema information for LLM context"""
        return """
DATABASE SCHEMA:

1. observations (galaxy observation records)
   - id (INTEGER): internal ID
   - observation_id (TEXT): e.g., "GCSO-J1951-0258"
   - ra (REAL): Right Ascension in degrees
   - dec (REAL): Declination in degrees
   - survey_source (TEXT): e.g., "DESI DR10", "SDSS9"
   - captured_at (TIMESTAMP): when observed
   - fov (REAL): Field of view in degrees

2. classifications (ML model predictions)
   - id (INTEGER): internal ID
   - observation_id (INTEGER): foreign key to observations.id
   - model_version (TEXT): model filename/version
   - predicted_class (TEXT): "Disturbed / Merging", "Smooth", "Spiral", "Edge-on"
   - confidence (REAL): 0.0 to 1.0
   - classified_at (TIMESTAMP): when classified
   - is_manual_override (BOOLEAN): user corrected this
   - manual_class (TEXT): user's correction if overridden

3. astronomical_metadata (catalog data)
   - id (INTEGER): internal ID
   - observation_id (INTEGER): foreign key to observations.id
   - catalog_source (TEXT): e.g., "NOIRLab TAP", "Legacy Survey"
   - object_type (TEXT): "GALAXY", "STAR", "QUASAR"
   - redshift (REAL): cosmological redshift
   - u_magnitude, g_magnitude, r_magnitude, i_magnitude, z_magnitude (REAL): photometry
   - metadata_json (TEXT): additional JSON data

4. chat_sessions
   - id (INTEGER): internal ID
   - session_id (TEXT): unique session identifier
   - title (TEXT): session title

5. chat_messages
   - id (INTEGER): internal ID
   - session_id (INTEGER): foreign key to chat_sessions.id
   - role (TEXT): "user" or "assistant"
   - content (TEXT): message text

COMMON QUERIES:
- Find galaxies by classification: SELECT * FROM observations o JOIN classifications c ON o.id = c.observation_id WHERE c.predicted_class = 'Spiral'
- Count by class: SELECT predicted_class, COUNT(*) FROM classifications GROUP BY predicted_class
- High confidence observations: SELECT * FROM observations o JOIN classifications c ON o.id = c.observation_id WHERE c.confidence > 0.9
- Manual overrides: SELECT * FROM classifications WHERE is_manual_override = TRUE
        """

    def execute_query(self, sql: str, params: List = None) -> Dict[str, Any]:
        """Safely execute a read-only SELECT query.
        
        Returns:
            {
                'success': bool,
                'rows': List[Dict],
                'count': int,
                'error': str or None,
                'columns': List[str]
            }
        """
        # Security: only allow SELECT queries
        if not sql.strip().upper().startswith('SELECT'):
            return {
                'success': False,
                'error': 'Only SELECT queries are allowed',
                'rows': [],
                'count': 0,
                'columns': []
            }

        conn = self.get_connection()
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or [])
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Convert to list of dicts
            result_rows = [dict(row) for row in rows]
            
            return {
                'success': True,
                'rows': result_rows,
                'count': len(result_rows),
                'columns': columns,
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'rows': [],
                'count': 0,
                'columns': []
            }
        finally:
            conn.close()

    def delete_all_observations(self):
        """Delete all observations and related data."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_feedback")
            cursor.execute("DELETE FROM astronomical_metadata")
            cursor.execute("DELETE FROM classifications")
            cursor.execute("DELETE FROM observations")
            conn.commit()
        finally:
            conn.close()

    def save_user_feedback(self, observation_id: int, original_prediction: str,
                          user_correction: str, feedback_type: str = "correction",
                          comments: str = None):
        """Save user feedback/corrections"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_feedback (observation_id, original_prediction,
                                         user_correction, feedback_type, comments)
                VALUES (?, ?, ?, ?, ?)
            """, (observation_id, original_prediction, user_correction,
                  feedback_type, comments))
            conn.commit()
        finally:
            conn.close()

    def get_image_data(self, observation_id: str) -> Optional[bytes]:
        """Get image blob data for an observation"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT image_data FROM observations WHERE observation_id = ?
            """, (observation_id,))

            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()
