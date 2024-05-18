from flask import Flask, request, jsonify
from transformers import pipeline
import time
import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = "0"

app = Flask(__name__)
model = None

def load_model():
    """Load the model and assign to global variable."""
    global model
    if model is None:
        print("Loading the transcription model...")
        start_time = time.time()
        try:
            # Attempt to load the model
            model = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-base", framework="pt")
            load_time = time.time() - start_time
            print(f"Model loaded in {load_time:.2f} seconds.")
        except Exception as e:
            print(f"Failed to load model: {e}")
            model = None  # Ensure model is set to None if loading fails

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Handle transcription requests."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        audio_path = './temp_audio.wav'
        file.save(audio_path)
        start_time = time.time()
        transcription = model(audio_path)
        print("Transcribe finished in {:.2f} seconds.".format(time.time() - start_time))
        os.remove(audio_path)
        return jsonify({"transcription": transcription})

if __name__ == "__main__":
    load_model()  # Load model before starting the server
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)