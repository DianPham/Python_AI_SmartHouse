import os
from pydub import AudioSegment

# Directory containing your m4a files
m4a_directory = r"C:/Users/DELL.DESKTOP-TETDMA3/Downloads/new_word/hai"  # Change this to your directory containing M4A files
output_directory = r"C:/Users/DELL.DESKTOP-TETDMA3/Downloads/new_word/hai"  # Directory to save WAV files

# Create output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Iterate through each file in the m4a directory
for filename in os.listdir(m4a_directory):
    if filename.endswith('.m4a'):
        # Path to the M4A file
        m4a_path = os.path.join(m4a_directory, filename)
        
        # Load the M4A file
        audio = AudioSegment.from_file(m4a_path, format='m4a')
        
        # Create the new filename by changing the extension to .wav
        wav_filename = os.path.splitext(filename)[0] + '.wav'
        wav_path = os.path.join(output_directory, wav_filename)
        
        # Export the file in WAV format
        audio.export(wav_path, format='wav')
        
        print(f"Converted {filename} to {wav_filename}")

print("Conversion completed!")
