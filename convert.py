import json
import yaml

# Load the JSON data
filename = "vietnamese_artists_songs.json"
with open(filename, "r", encoding="utf-8") as file:
    json_data = json.load(file)

# Convert to YAML
yaml_data = yaml.dump(json_data, allow_unicode=True, default_flow_style=False)

# Save to a .yml file
with open("vietnamese_artists_songs.yml", "w", encoding="utf-8") as file:
    file.write(yaml_data)
