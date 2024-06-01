import os

# Define the directory containing your audio files
directory = 'C:\\Dian\\SmartHouse\\Test\\PhoWhisper\\test_set\\audio'
script_dir = 'C:\\Dian\\SmartHouse\\Test\\PhoWhisper\\test_set\\transcripts'

# Mapping of keywords in filenames to content for script files

def is_long(filename):
    return 'long' in filename

# Iterate over each file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.wav') and is_long(filename):

        content = 'Làm ơn mở đèn phòng khách cho tôi'

        # Define the name of the new script file
        script_filename = os.path.splitext(filename)[0] + '.txt'

        # Path for the new script file
        script_path = os.path.join(script_dir, script_filename)

        # Write the content to the script file
        with open(script_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Created script file {script_filename} with content: "{content}"')