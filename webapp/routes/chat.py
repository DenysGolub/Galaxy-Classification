from flask import request, Response, jsonify
from galaxy_classification.database import GalaxyDatabase
from webapp.services.chat_service import ChatService

db = GalaxyDatabase()
chat_service = ChatService()

def register_chat_routes(app):
    @app.route('/api/chat/history/<session_id>', methods=['GET'])
    def get_chat_history(session_id):
        """Get chat history for a session"""
        session_pk = db.get_or_create_chat_session(session_id, "GCS Assistant Session")
        messages = db.get_chat_history(session_pk)
        return jsonify(messages)

    @app.route('/api/chat/sessions', methods=['GET'])
    def list_chat_sessions():
        """List all saved chat sessions."""
        sessions = db.get_chat_sessions()
        return jsonify(sessions)

    @app.route('/chat', methods=['POST'])
    def chat():
        user_message = request.json.get("message")
        session_id = request.json.get("session_id", "default")
        mode = request.json.get("mode", "expert")  

        session_pk = db.get_or_create_chat_session(session_id, "GCS Assistant Session")

        db.save_chat_message(session_pk, "user", user_message)

        if mode == "database":
            database_response = chat_service.get_dynamic_database_response(user_message)
            if database_response is not None:
                db.save_chat_message(session_pk, "assistant", database_response)
                return Response(
                    database_response,
                    mimetype='text/plain',
                    headers={'X-DB-Query': 'true', 'X-Response-Mode': 'database'}
                )

        response_generator = chat_service.generate_response(user_message, session_id, mode=mode)

        def generate():
            full_response = ""
            for token in response_generator:
                full_response += token
                yield token

            db.save_chat_message(session_pk, "assistant", full_response)

        return Response(generate(), mimetype='text/plain', headers={'X-Response-Mode': mode})
