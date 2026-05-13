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

    def save_chat_message(
    self,
    session_id,
    role,
    content,
    tokens_used=None
):

        if isinstance(content, (dict, list)):

            content = json.dumps(
                content,
                indent=2,
                default=str
            )

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO chat_messages (
            session_id,
            role,
            content,
            tokens_used
        )
        VALUES (?, ?, ?, ?)
        """, (
            session_id,
            role,
            content,
            tokens_used
        ))

        conn.commit()

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
