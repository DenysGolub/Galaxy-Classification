import requests
import json

class ChatService:
    def __init__(self):
        self.OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
        self.MODEL_NAME = "llama3"

    def generate_response(self, user_message, session_id="default"):
        """Generate AI response using Ollama"""
        system_persona = (
            "You are the GCI Neural Intelligence, the primary AI core of the Galactic Discovery Vessel. "
            "Your personality is highly intelligent, stoic, and helpful. You are an expert in astrophysics "
            "and galactic classification. Use space-themed terminology. "
            "Give concise, technical, and futuristic answers."
        )

        payload = {
            "model": self.MODEL_NAME,
            "prompt": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_persona}<|eot_id|>"
                      f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"
                      f"<|start_header_id|>assistant<|end_header_id|>\n\n",
            "stream": True
        }

        def generate():
            try:
                full_response = ""
                with requests.post(self.OLLAMA_URL, json=payload, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if line:
                            chunk = json.loads(line.decode('utf-8'))
                            token = chunk.get("response", "")
                            full_response += token
                            yield token
                            if chunk.get("done"):
                                break

                return full_response

            except requests.exceptions.ConnectionError:
                error_msg = "[Error: Ollama server not detected. Ensure 'ollama serve' is running.]"
                yield error_msg
            except Exception as e:
                error_msg = f"[System Error: {str(e)}]"
                yield error_msg

        return generate()