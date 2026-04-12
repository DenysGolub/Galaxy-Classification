import io
import base64
import requests
import torch
import os
from flask import Flask, Response, json, render_template, request, jsonify
from flask_cors import CORS 
from PIL import Image
import torchvision.transforms as transforms
import sys

sys.path.append(os.path.abspath('.'))
from galaxy_source.galaxy_cnn import GalaxyCNN

app = Flask(__name__)
CORS(app) 

model = GalaxyCNN()
try:
    model.load_state_dict(torch.load('models/cnn_85_accuracy.pth', map_location='cpu'))
    model.eval()
    print("AI CORE: Neural weights loaded successfully.")
except Exception as e:
    print(f"FATAL: Could not load model: {e}")

CLASSES = ["Disturbed / Merging", "Smooth", "Spiral", "Edge-on"]

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/legacy")
def legacy_proxy():
    ra = request.args.get("ra")
    dec = request.args.get("dec")
    radius = request.args.get("radius", "0.02")

    url = f"https://www.legacysurvey.org/viewer/tractor-cutout.json?ra={ra}&dec={dec}&radius={radius}"

    try:
        r = requests.get(url, timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)})



@app.route('/predict', methods=['POST'])
def predict():
    print("SIGNAL RECEIVED: Processing frame...") # Debug log
    try:
        data = request.json['image']
        header, encoded = data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        # Matches the size your model expects
        preprocess = transforms.Compose([
            transforms.Resize((256, 256)), 
            transforms.ToTensor(),
        ])
        
        input_tensor = preprocess(img).unsqueeze(0)

        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, index = torch.max(probabilities, 0)

        result = {
            "prediction": CLASSES[index.item()],
            "confidence": round(confidence.item() * 100, 2),
            "status": "success"
        }
        print(f"ANALYSIS COMPLETE: {result['prediction']}")
        return jsonify(result)

    except Exception as e:
        print(f"CORE ERROR: {str(e)}")
        return jsonify({"error": str(e), "status": "fail"}), 400

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

MODEL_NAME = "llama3"

CLASSES = ["Disturbed / Merging", "Smooth", "Spiral", "Edge-on"]

@app.route('/')

def index():

    return render_template('index.html')

@app.route('/assistant')

def assistant_page():
    return render_template('assistant.html')

@app.route('/chat', methods=['POST'])

def chat():

    user_message = request.json.get("message")
    system_persona = (
        "You are the GCI Neural Intelligence, the primary AI core of the Galactic Discovery Vessel. "
        "Your personality is highly intelligent, stoic, and helpful. You are an expert in astrophysics "
        "and galactic classification. Use space-themed terminology. "
        "Give concise, technical, and futuristic answers."
    )
    payload = {
        "model": MODEL_NAME,
        "prompt": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_persona}<|eot_id|>"

                  f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"

                  f"<|start_header_id|>assistant<|end_header_id|>\n\n",
        "stream": True
    }

    def generate():
        try:
            with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        token = chunk.get("response", "")
                        yield token
                        if chunk.get("done"):
                            break

        except requests.exceptions.ConnectionError:
            yield "[Error: Ollama server not detected. Ensure 'ollama serve' is running.]"
        except Exception as e:
            yield f"[System Error: {str(e)}]"

    return Response(generate(), mimetype='text/plain')


if __name__ == '__main__':
    app.run(debug=True, port=5000)