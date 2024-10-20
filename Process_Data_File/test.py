from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import os

def trim_audio_automatically(file_path, output_path, silence_thresh=-70, min_silence_len=400, padding=200):
    """
    Automatically trims silence from the start and end of an audio file.
    
    :param file_path: Path to the input audio file (wav or m4a, etc.)
    :param output_path: Path to save the trimmed audio file
    :param silence_thresh: Silence threshold in dBFS (decibels below the maximum volume)
    :param min_silence_len: Minimum length of silence to be considered silence (in ms)
    """
    # Load the audio file
    audio = AudioSegment.from_file(file_path)

    # Detect non-silent chunks [(start, end), (start, end), ...]
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

    if nonsilent_ranges:
        
        start_trim = max(nonsilent_ranges[0][0] - padding, 0)  # Start of the first non-silent segment with padding
        end_trim = min(nonsilent_ranges[-1][1] + padding, len(audio))  # End of the last non-silent segment with padding

        # Trim the audio based on detected speech
        trimmed_audio = audio[start_trim:end_trim]

        # Export the trimmed audio
        trimmed_audio.export(output_path, format="wav")
        print(f"Trimmed audio saved to {output_path}")
    else:
        print("No speech detected, skipping.")


# Example usage for normalizing multiple files
audio_dir = "C:/Dian/Data/norm_audio_2"
output_dir = "C:/Dian/Data/trimmed_audio"

for audio_file in os.listdir(audio_dir):
    if audio_file.endswith(".wav"):  # Assuming the files are in WAV format
        input_path = os.path.join(audio_dir, audio_file)
        output_path = os.path.join(output_dir, audio_file)
        trim_audio_automatically(input_path, output_path)
