import os
import json

# Define the directory containing your audio files
directory = 'C:/Dian/Data/audio'
script_dir = 'C:\\Dian\\SmartHouse\\Test\\PhoWhisper\\test_set\\transcripts'

# Load the JSON file that contains the mapping of sanitized words to original words
json_file_path = 'C:\\Dian\\SmartHouse\\Test\\PhoWhisper\\sanitized_mapping.json'

# Load the mapping from the JSON file
with open(json_file_path, 'r', encoding='utf-8') as json_file:
    sanitized_mapping = json.load(json_file)

# Helper function to get transcript from sanitized filename
def get_transcript_from_filename(filename, mapping):
    # Split the filename and find the corresponding words in the JSON mapping
    words = filename.split('_')
    transcript = []

    # Loop over each part of the filename and map it to the original word
    if words[3] in mapping:
        transcript.append(mapping[words[3]] + '.')
    
    # Join the mapped words to form the transcript sentence
    return ' '.join(transcript)
try:
    # Iterate over each file in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.m4a'):
            # Remove the .wav extension to work with the sanitized name
            sanitized_name = os.path.splitext(filename)[0]

            # Get the transcript using the sanitized name
            transcript = get_transcript_from_filename(sanitized_name, sanitized_mapping)

            # Define the name of the new script file
            script_filename = sanitized_name + '.txt'

            # Path for the new script file
            script_path = os.path.join(script_dir, script_filename)

            # Write the content to the script file
            with open(script_path, 'w', encoding='utf-8') as file:
                file.write(transcript)
            #print(f'Created script file {script_filename} with content: "{transcript}"')
except Exception as e:
    print(e)
