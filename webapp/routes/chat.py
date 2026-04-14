from flask import request, Response, jsonify
from galaxy_classification.database import GalaxyDatabase
from webapp.services.chat_service import ChatService

db = GalaxyDatabase()
chat_service = ChatService()

def register_chat_routes(app):
    @app.route('/api/chat/history/<session_id>', methods=['GET'])
    def get_chat_history(session_id):
        """Get chat history for a session"""
        session_pk = db.get_or_create_chat_session(session_id, "GCI Assistant Session")
        messages = db.get_chat_history(session_pk)
        return jsonify(messages)

    @app.route('/chat', methods=['POST'])
    def chat():
        """Handle chat messages with AI assistant"""
        user_message = request.json.get("message")
        session_id = request.json.get("session_id", "default")

        # Ensure session exists and get its integer primary key
        session_pk = db.get_or_create_chat_session(session_id, "GCI Assistant Session")

        # Save user message
        db.save_chat_message(session_pk, "user", user_message)

        # Generate response
        response_generator = chat_service.generate_response(user_message, session_id)

        def generate():
            full_response = ""
            for token in response_generator:
                full_response += token
                yield token

            # Save AI response to database
            db.save_chat_message(session_pk, "assistant", full_response)

        return Response(generate(), mimetype='text/plain')