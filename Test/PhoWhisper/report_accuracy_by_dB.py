import io
import os
import re
import subprocess
import sys
import time
import pandas as pd
from jiwer import wer
from matplotlib import pyplot as plt
import requests

# Set stdout to handle Unicode output correctly
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define paths using os.path.join for compatibility across OSes
current_dir = "C:\\Dian\\SmartHouse"
path_to_python = os.path.join(current_dir, "venv", "Scripts", "python.exe")
path_to_init_server = os.path.join(current_dir, "PhoWhisper_Server", "init_server.py")
audio_dir = os.path.join(current_dir, "Test", "PhoWhisper", "test_set", "audio_with_noise")
transcript_dir = os.path.join(current_dir, "Test", "PhoWhisper", "test_set", "transcripts")
result_path = os.path.join(current_dir, "Test", "PhoWhisper", "result.txt")
aggregate_result_path = os.path.join(current_dir, "Test", "PhoWhisper", "aggregate_results_accuracy.csv")

def start_server():
    """Start the Flask server using a subprocess."""
    process = subprocess.Popen([path_to_python, path_to_init_server])
    return process

def get_noise_level(filename):
    match = re.search(r'_with_noise_(\d+)dB\.wav', filename)
    return int(match.group(1)) if match else None

def get_script_name(filename):
    """Extract base script name from filename."""
    match = re.match(r'(.*?)_with_noise_', filename)
    return match.group(1) if match else None

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
                return f"Error in transcription response: {response.json().get('error', {})}"
    except requests.RequestException as e:
        return f"Request failed: {str(e)}"



def plot_results(data):
    plt.figure(figsize=(10, 6))
    plt.plot(data['noise_level'], data['accuracy'], marker='o', linestyle='-')
    plt.title('Average Accuracy by Noise Level')
    plt.xlabel('Noise Level')
    plt.ylabel('Average Accuracy')
    plt.ylim(0, 1.1)
    plt.grid(True)
    plt.show()


def main():
    # server_process = start_server()
    # time.sleep(10)
    # results = []

    # for filename in os.listdir(audio_dir):
    #     if filename.endswith('.mp3') or filename.endswith('.wav'):
    #         print(f"Processing {filename}")
    #         audio_path = os.path.join(audio_dir, filename)
    #         transcript_path = os.path.join(transcript_dir, get_script_name(filename) + '.txt')

    #         # Transcribe audio
    #         start_time = time.time()
    #         transcription = send_audio_to_server(audio_path)
    #         total_time = time.time() - start_time

    #         # Read ground truth transcription
    #         if os.path.exists(transcript_path):
    #             with open(transcript_path, 'r', encoding='utf-8') as file:
    #                 ground_truth = file.read().strip()

    #             # Compute the word error rate
    #             error_rate = wer(ground_truth.lower(), transcription)
    #             content = f"{filename}: \nTranscription: {transcription}\nGround Truth: {ground_truth}\nWord Error Rate: {error_rate}\nTranscription Time: {total_time:.2f} seconds\n\n\n"
    #             with open(result_path, 'a', encoding='utf-8') as file:
    #                 file.write(content)
    #             results.append({'noise_level': get_noise_level(filename), 'accuracy': 1 - error_rate})
    #         else:
    #             print(f"Transcript file not found for {filename}")

    # if results:
    #     df = pd.DataFrame(results)
    #     average_df = df.groupby('noise_level').agg({'accuracy': 'mean'}).reset_index()
    #     average_df.to_csv(aggregate_result_path, index=False)
    data = pd.read_csv(aggregate_result_path)
    plot_results(data)
    # server_process.terminate()

if __name__ == "__main__":
    main()
