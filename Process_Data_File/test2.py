import requests
import json
from unidecode import unidecode
from pydub import AudioSegment
from io import BytesIO
import os

# Define the URL for the speech synthesis API
url = "https://viettelai.vn/tts/speech_synthesis"

# Define headers
headers = {
    'accept': '*/*',
    'Content-Type': 'application/json'
}

# Your token (replace with the actual token)
token = "36c1bbbf0afd3e5266ca70d578bccec5"

# Define the output folder
output_folder = r"C:/Users/DELL.DESKTOP-TETDMA3/Downloads/new_word/chi"
# Create the output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Open the file and read words
with open('C:/Users/DELL.DESKTOP-TETDMA3/Downloads/name2.txt', 'r', encoding='utf-8') as file:
    words = [line.strip() for line in file]

# Loop through each word and send a request to the API
for word in words:
    payload = json.dumps({
        "text": word,
        "voice": "hn-thaochi",
        "speed": 1,
        "tts_return_option": 3,
        "token": token,
        "without_filter": True 
    },ensure_ascii=False)
    
     # Encode the payload in UTF-8 before sending it
    payload = payload.encode('utf-8')  # Explicitly encode payload as UTF-8
    
    # Send the request to the API
    response = requests.request("POST", url, headers=headers, data=payload)
    
    # Ensure the response is valid before proceeding    
    if response.status_code == 200:
        # Load the response content directly into pydub via BytesIO
        mp3_audio = AudioSegment.from_file(BytesIO(response.content), format="mp3")
        
        # Convert the MP3 content to M4A format
        sanitized_word = unidecode(word).lower().replace(' ', '')
        m4a_filename = os.path.join(output_folder, f"nu_chi_bac_{sanitized_word}.m4a")
        
        # Export the audio as M4A with AAC codec
        mp3_audio.export(m4a_filename, format="ipod", codec="aac") 
        
        print(f"Audio saved as '{m4a_filename}'.")
    else:
        print(f"Request failed with status code {response.status_code}")
        print(f"Error: {response.text}")