import os
from pydub import AudioSegment

def format_time(seconds):
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"

def merge_vtt_files(vtt_files, output_vtt):
    total_time = 0.0
    merged_content = "WEBVTT\n\n"

    for vtt_file in vtt_files:
        with open(vtt_file, 'r', encoding= 'utf-8') as file:
            lines = file.readlines()
            for line in lines:
                if '-->' in line:
                    start_time, end_time = line.split(" --> ")
                    # Calculate new time range
                    start_seconds = total_time
                    end_seconds = total_time + float(end_time.split(':')[-1].replace(',', '.'))
                    
                    merged_content += f"{format_time(start_seconds)} --> {format_time(end_seconds)}\n"
                    total_time = end_seconds
                else:
                    if line.strip() != "WEBVTT" and line.strip():
                        merged_content += line
            merged_content += "\n"

    with open(output_vtt, 'w', encoding='utf-8') as out_file:
        out_file.write(merged_content)


def merge_audio_files(audio_files, output_audio):
    combined = AudioSegment.empty()
    
    for audio_file in audio_files:
        audio_segment = AudioSegment.from_wav(audio_file)
        combined += audio_segment
    
    combined.export(output_audio, format="wav")

# Directory containing audio files
audio_dir = "C:/Dian/Data/test_set"
audio_files = [os.path.join(audio_dir, f) for f in sorted(os.listdir(audio_dir)) if f.endswith(".wav")]

# Merge audio files
merge_audio_files(audio_files, "C:/Dian/Data/merged_audio.wav")


# Directory containing the VTT files
vtt_dir = "C:/Dian/Data/test_set"
vtt_files = [os.path.join(vtt_dir, f) for f in sorted(os.listdir(vtt_dir)) if f.endswith(".vtt")]

# Merge VTT files
merge_vtt_files(vtt_files, "C:/Dian/Data/merged.vtt")
