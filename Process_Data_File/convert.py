import os
from unidecode import unidecode
import re

# Define folder containing the files to be renamed and the name of the text file
folder_path = "C:/Users/DELL.DESKTOP-TETDMA3/Downloads/dat"  # Replace with the path to your folder containing the .m4a files
names_file = "C:/Users/DELL.DESKTOP-TETDMA3/Downloads/name2.txt"  # Replace with the path to your names file

# Read the names from the text file
with open(names_file, 'r', encoding='utf-8') as file:
    new_names = [line.strip() for line in file.readlines() if line.strip()]

# Get all files in the folder that match the original naming pattern and sort them numerically
def extract_number(filename):
    match = re.search(r'(\d+)', filename)  # Look for numbers directly, without parentheses
    return int(match.group(1)) if match else float('inf')  # If no match, assign infinity for sorting

files = sorted([f for f in os.listdir(folder_path) if f.endswith(".wav")], key=extract_number)

# Ensure that the number of new names matches the number of files
if len(new_names) != len(files):
    print(len(new_names))
    print(len(files))
    print("The number of new names does not match the number of files.")
else:
    # Iterate over the files and rename them with the corresponding new name
    for index, file_name in enumerate(files):
        # Remove accents from the new name
        new_name = unidecode(new_names[index]).lower().replace(' ', '')
        new_file_name = f"nam_dat_trung_{new_name}.wav"
        old_file_path = os.path.join(folder_path, file_name)
        new_file_path = os.path.join(folder_path, new_file_name)

        # Rename the file
        os.rename(old_file_path, new_file_path)
        print(f"Renamed '{file_name}' to '{new_file_name}'")
    print("Renaming completed.")
