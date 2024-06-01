import io
import os
import subprocess
import sys
import threading
import time
from jiwer import wer
import requests

# Set stdout to handle Unicode output correctly
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define paths using os.path.join to ensure compatibility across OSes
current_dir = "C:\\Dian\\SmartHouse"
path_to_python = os.path.join(current_dir, "venv", "Scripts", "python.exe")
path_to_init_server = os.path.join(current_dir, "PhoWhisper_Server", "init_server.py")
audio_dir = os.path.join(current_dir, "Test", "PhoWhisper", "test_set", "audio")
transcript_dir = os.path.join(current_dir, "Test", "PhoWhisper", "test_set", "transcripts")
result_path = "C:\\Dian\\SmartHouse\\Test\\PhoWhisper\\result.txt"

def start_server():
    """Start the Flask server using a subprocess."""
    print(f"Starting server using {path_to_init_server}")
    process = subprocess.Popen([path_to_python, path_to_init_server])
    return process  # Return the process to possibly manage it later

def send_audio_to_server(audio_path):
    """Send the audio file to the Flask server for transcription."""
    url = 'http://localhost:5000/transcribe'
    try:
        with open(audio_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(url, files=files)
            if response.status_code == 200:
                transcription_result = response.json().get('transcription', {}).get('text', '')
                return transcription_result
            else:
                return "Error in transcription response"
    except requests.RequestException as e:
        return f"Request failed: {str(e)}"

def main():
    server_process = start_server()  # Start server and keep the process
    time.sleep(10)  # Wait for the server to start

    for filename in os.listdir(audio_dir):
        if filename.endswith('.mp3') or filename.endswith('.wav'):
            print(f"Processing {filename}")
            audio_path = os.path.join(audio_dir, filename)
            transcript_path = os.path.join(transcript_dir, os.path.splitext(filename)[0] + '.txt')

            # Transcribe audio
            start_time = time.time()
            transcription = send_audio_to_server(audio_path)
            finish_time = time.time() - start_time

            # Read ground truth transcription
            if os.path.exists(transcript_path):
                with open(transcript_path, 'r', encoding='utf-8') as file:
                    ground_truth = file.read().strip()

                # Compute the word error rate
                error_rate = wer(ground_truth.lower(), transcription)
                content = f"{filename}: \nTranscription: {transcription}\nGround Truth: {ground_truth}\nWord Error Rate: {error_rate}\nTranscription Time: {finish_time:.2f} seconds\n\n\n"
                with open(result_path, 'a', encoding='utf-8') as file:
                    file.write(content)
            else:
                print(f"Transcript file not found for {filename}")

    server_process.terminate()  # Optionally terminate the server when done

if __name__ == "__main__":
    main()
