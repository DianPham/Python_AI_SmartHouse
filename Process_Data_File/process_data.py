import os
import json
import requests
import time
from jiwer import wer

current_dir = "C:\\Dian\\SmartHouse"
# Directory containing audio files and the path to the transcript JSON file
transcript_file = "C:\\Dian\\SmartHouse\\Test\\PhoWhisper\\sanitized_mapping.json"
result_path = os.path.join(current_dir, "Test", "PhoWhisper", "result.txt")
input_dir = "C:/Dian/Data/norm_audio"
output_dir = "C:/Dian/Data/vtt"
token = "36c1bbbf0afd3e5266ca70d578bccec5"


def send_audio_to_server(audio_path):
    """Send the file path to the Flask server for transcription."""
    url = "https://viettelai.vn/asr/recognize"
    try:
        
        payload={'token': token}
        files=[
            ('file',('$AUDIO_FILE',open(audio_path,'rb'),'audio/wav'))
        ]
        
        headers = {
            'accept': '*/*'
        }
                
        if not os.path.exists(audio_path):
            return f"Error: File does not exist at {audio_path}"
        
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        
        if response.status_code == 200:
            return response.text
        else:
            return f"Error in transcription response: {response.json().get('error', {})}"
    except requests.RequestException as e:
        return f"Request failed: {str(e)}"

def process(audio_path, ground_truth, filename):
    try:
        # Transcribe audio
        start_time = time.time()
        transcription = send_audio_to_server(audio_path)
        total_time = time.time() - start_time
        
        if transcription:
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
            print(f"Can not get transcript for {filename}")
    except Exception as e:
        print(e)


# Load the transcripts from the JSON file
# Load the mapping from the JSON file
with open(transcript_file, 'r', encoding='utf-8') as json_file:
    transcripts = json.load(json_file)

# Create VTT files for all audio files, extracting the key from the file name
for audio_file in os.listdir(input_dir):
    if audio_file.endswith(".wav"):  # Adjust this if the file extension differs
        # Extract the suffix (e.g., 'moden' from 'nu_chi_bac_moden.m4p')
        file_key = os.path.splitext(audio_file)[0].split('_')[-1]
        transcript = transcripts.get(file_key, "Unknown")
        process(os.path.join(input_dir, audio_file), transcript, audio_file)