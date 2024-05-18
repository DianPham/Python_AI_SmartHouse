import shutil
from transformers import file_utils

# Get the default cache directory path
cache_dir = file_utils.default_cache_path

# Remove the entire cache directory
shutil.rmtree(cache_dir)

# Optionally, recreate the cache directory if you plan to use it immediately after