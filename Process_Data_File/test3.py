import os

# Define the directory containing your files
directory = r"C:/Users/DELL.DESKTOP-TETDMA3/Downloads/new_word/thanhha"  # Change this to your actual directory

# Define the old prefix and the new prefix
old_prefix = 'nu_chi_bac_'
new_prefix = 'nu_thanha_bac_'

# Iterate through each file in the directory
for filename in os.listdir(directory):
    # Check if the filename starts with the old prefix
    if filename.startswith(old_prefix):
        # Create the new filename by replacing the old prefix with the new one
        new_filename = filename.replace(old_prefix, new_prefix, 1)
        
        # Define the full paths for the old and new filenames
        old_file_path = os.path.join(directory, filename)
        new_file_path = os.path.join(directory, new_filename)
        
        # Rename the file
        os.rename(old_file_path, new_file_path)
        print(f'Renamed {filename} to {new_filename}')