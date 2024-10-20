from pydub import AudioSegment
import os
import json

def get_audio_duration(file_path):
    audio = AudioSegment.from_file(file_path, format="m4a")  # Specify M4A format
    return len(audio) / 1000.0  # Convert milliseconds to seconds

def create_vtt(audio_file, transcript, output_vtt):
    duration = get_audio_duration(audio_file)
    end_time = f"00:00:{duration:06.3f}".replace('.', ',')
    
    vtt_content = f"WEBVTT\n\n00:00:00.000 --> {end_time}\n{transcript}\n"
    
    with open(output_vtt, 'w', encoding='utf-8') as vtt_file:
        vtt_file.write(vtt_content)

# Directory containing audio files and the path to the transcript JSON file
audio_dir = "C:/Dian/Data/validate_set"
transcript_file = "C:/Dian/SmartHouse/Test/PhoWhisper/sanitized_mapping.json"
output_dir = "C:/Dian/Data/validate_set"

# Load the transcripts from the JSON file
with open(transcript_file, 'r', encoding='utf-8') as f:
    transcripts = json.load(f)

# Create VTT files for all audio files, extracting the key from the file name
for audio_file in os.listdir(audio_dir):
    if audio_file.endswith(".wav"):  # Adjust this if the file extension differs
        # Extract the suffix (e.g., 'moden' from 'nu_chi_bac_moden.m4a')
        file_key = os.path.splitext(audio_file)[0].split('_')[-1]
        transcript = transcripts.get(file_key, "Unknown")
        output_vtt = os.path.join(output_dir, os.path.splitext(audio_file)[0] + ".vtt") 
        create_vtt(os.path.join(audio_dir, audio_file), transcript, output_vtt)
