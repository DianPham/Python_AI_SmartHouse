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
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set stdout to handle Unicode output correctly
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define paths using os.path.join for compatibility across OSes
current_dir = "C:\\Dian\\SmartHouse"
audio_dir = os.path.join(current_dir, "Test", "PhoWhisper", "test_set", "audio")
transcript_dir = os.path.join(current_dir, "Test", "PhoWhisper", "test_set", "transcripts")
result_path = os.path.join(current_dir, "Test", "PhoWhisper", "result.txt")
aggregate_result_path = os.path.join(current_dir, "Test", "PhoWhisper", "aggregate_results_accuracy.csv")

# Set to track processed files to avoid duplicates
processed_files = set()

def send_audio_to_server(audio_path):
    """Send the file path to the Flask server for transcription."""
    url = 'http://localhost:5000/transcribe'
    try:
        if not os.path.exists(audio_path):
            return f"Error: File does not exist at {audio_path}"

        # Send the file path in JSON format
        data = {"file_path": audio_path}
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            transcription_result = response.json().get('transcription', {}).get('text', '')
            return transcription_result
        else:
            return f"Error in transcription response: {response.json().get('error', {})}"
    except requests.RequestException as e:
        return f"Request failed: {str(e)}"


def process_audio_file(filename):
    """Process a single audio file, send it to the server and calculate WER."""
    if filename.endswith('.m4a') and filename not in processed_files:
        print(f"Processing {filename}")
        processed_files.add(filename)  # Track the file to prevent duplication
        audio_path = os.path.join(audio_dir, filename)
        transcript_path = os.path.join(transcript_dir, filename.split(".")[0] + '.txt')

        # Transcribe audio
        start_time = time.time()
        transcription = send_audio_to_server(audio_path)
        total_time = time.time() - start_time

        # Read ground truth transcription
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as file:
                ground_truth = file.read().strip()

            # Compute the word error rate
            error_rate = wer(ground_truth.lower(), transcription)

            # If WER is greater than 0, print the filename and save the result
            if error_rate > 0:
                print(f"Filename with WER > 0: {filename}")
                # Write to result file
                content = f"{filename}: \nTranscription: {transcription}\nGround Truth: {ground_truth}\nWord Error Rate: {error_rate}\nTranscription Time: {total_time:.2f} seconds\n\n\n"
                with open(result_path, 'a', encoding='utf-8') as file:
                    file.write(content)

        else:
            print(f"Transcript file not found for {filename}")


def main():
    # Use ThreadPoolExecutor to handle multiple audio files concurrently
    with ThreadPoolExecutor(max_workers=4) as executor:  # Adjust max_workers based on system resources
        futures = [executor.submit(process_audio_file, filename) for filename in os.listdir(audio_dir)]
        
        # Wait for all tasks to complete
        for future in as_completed(futures):
            try:
                future.result()  # Get the result of the task
            except Exception as exc:
                print(f"Generated an exception: {exc}")

if __name__ == "__main__":
    main()
