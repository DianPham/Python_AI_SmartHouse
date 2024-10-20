from flask import Flask, request, jsonify
from transformers import pipeline
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor  # For handling multiple threads

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from VoiceAssistant.voice import speak

os.environ['TF_ENABLE_ONEDNN_OPTS'] = "0"

app = Flask(__name__)
model = None

# Create a thread pool executor for handling concurrent requests
executor = ThreadPoolExecutor(max_workers=4)  # Adjust max_workers based on your machine

def load_model():
    """Load the model and assign to global variable."""
    global model
    if model is None:
        print("Loading the transcription model...")
        start_time = time.time()
        try:
            # Attempt to load the model
            model = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-medium", framework="pt")
            load_time = time.time() - start_time
            print(f"Model loaded in {load_time:.2f} seconds.")
        except Exception as e:
            print(f"Failed to load model: {e}")
            model = None  # Ensure model is set to None if loading fails

@app.route('/receive_reminder', methods=['POST'])
def receive_reminder():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    # Extract information from the received JSON payload
    task = data.get('task')

    # Use thread to handle speaking without blocking other requests
    executor.submit(speak, f"Đã đến giờ cho công việc {task}")

    return jsonify({'message': 'Reminder received successfully'}), 200

# @app.route('/transcribe', methods=['POST'])
# def transcribe():
#     """Handle transcription requests."""
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400

#     if file:
#         audio_path = './temp_audio.wav'
#         file.save(audio_path)
#         start_time = time.time()

#         # Run the transcription in a separate thread to prevent blocking
#         future = executor.submit(model, audio_path)
#         transcription = future.result()  # Wait for the transcription to complete

#         print("Transcribe finished in {:.2f} seconds.".format(time.time() - start_time))
#         #os.remove(audio_path)
#         return jsonify({"transcription": transcription})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Handle transcription requests via file path."""
    data = request.get_json()
    
    if not data or 'file_path' not in data:
        return jsonify({"error": "No file path provided"}), 400

    audio_path = data['file_path']
    
    # Check if the file exists before proceeding
    if not os.path.exists(audio_path):
        return jsonify({"error": f"File not found: {audio_path}"}), 400
    
    try:
        start_time = time.time()

        # Run the transcription in a separate thread to prevent blocking
        future = executor.submit(model, audio_path)
        transcription = future.result()  # Wait for the transcription to complete

        print("Transcription finished in {:.2f} seconds.".format(time.time() - start_time))

        return jsonify({"transcription": transcription})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    load_model()  # Load model before starting the server
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False, threaded=True)
