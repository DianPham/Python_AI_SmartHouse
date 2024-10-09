import geocoder

# Get location based on IP address
g = geocoder.ip('me')

# Print the latitude and longitude
print(f"Your current location is: {g.latlng}")